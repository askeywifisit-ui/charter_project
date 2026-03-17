#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdu_outlet1: Control LAB MSNSwitch/UIS PDU (HTTP API)
（含全域序列靜默，行為盡量與 pdu_outlet2.py 對齊：stale 清理 + 設定後自動清除）

CLI:
    python3 pdu_outlet1.py on
    python3 pdu_outlet1.py off
    python3 pdu_outlet1.py reset
    python3 pdu_outlet1.py status

API:
    from pdu_outlet1 import outlet1_control, get_status
    outlet1_control("on" / "off" / "reset")
    get_status()

環境變數（與 pdu_outlet2.py 對齊）：
    PDU_IP                   預設 "172.14.1.135"
    PDU_USER                 預設 "admin"
    PDU_PASS                 預設 "REPLACE_ME"
    PDU_OUTLET_ID            預設 "1"   (1-based)
    PDU_PROTOCOL             預設 "http"
    PDU_TIMEOUT              預設 "6"
    PDU_VERIFY_SSL           預設 0（http 不用；https 有自簽才需要 0）

    PDU_MUTE_SECS            預設 60（ON/RESET 會先靜默 N 秒）
    PDU_MUTE_AUTOCLEAR       預設 1（啟用：到期後自動 clear 自己設定的 serial.mute）
    PDU_MUTE_AUTOCLEAR_GRACE 預設 3（到期後多等 N 秒再嘗試清除，避免 race）

輸出/回傳（比照 pdu_outlet2.py，並向後相容）：
    outlet1_control() 回傳 dict：
      {
        "ok": bool,
        "outlet": [state_bool],         # 向後相容：舊 code 讀 js["outlet"][0]
        "mute_set": bool,
        "mute_until": int,
        "mute_left_sec": int,
        "resp": {...} | None,           # control 原始回應（若有）
        "status": {...} | None,         # /api/status 原始回應（若有）
        "error": "..." | None,
        "outlet_id": int
      }

備註：
- 本工具會寫 /home/da40/charter/var/serial.mute (epoch 秒) 作為全域靜默旗標。
- 只會清理「已過期」的 stale mute，不會清掉仍有效的 mute（避免干擾別的腳本）。
"""

import datetime
import os
import pathlib
import subprocess
import sys
import time
from typing import Any, Dict, Optional, Tuple

import requests


# ===== 依現場調整（可被環境變數覆蓋） =====
PDU_BRAND = "MSNSwitch/UIS"

PDU_IP = os.getenv("PDU_IP", "172.14.1.135")
PDU_USER = os.getenv("PDU_USER", "admin")
PDU_PASS = os.getenv("PDU_PASS", "REPLACE_ME")
PDU_PROTOCOL = os.getenv("PDU_PROTOCOL", "http")

PDU_TIMEOUT = int(os.getenv("PDU_TIMEOUT", "6"))
PDU_VERIFY_SSL = os.getenv("PDU_VERIFY_SSL", "0").strip().lower() in ("1", "true", "yes", "on")

try:
    OUTLET_ID = int(os.getenv("PDU_OUTLET_ID", "1"))
except Exception:
    OUTLET_ID = 1

# ======================================

# ---- 路徑 / 旗標檔（比照 pdu_outlet2.py）----
VAR_DIR = pathlib.Path("/home/da40/charter/var")
VAR_DIR.mkdir(parents=True, exist_ok=True)
MUTE_FILE = VAR_DIR / "serial.mute"
LOG_FILE = VAR_DIR / "pdu_mute.log"

MUTE_SECS = int(os.getenv("PDU_MUTE_SECS", "60"))
MUTE_AUTOCLEAR = os.getenv("PDU_MUTE_AUTOCLEAR", "1").strip().lower() not in ("0", "false", "no", "off")
MUTE_AUTOCLEAR_GRACE = int(os.getenv("PDU_MUTE_AUTOCLEAR_GRACE", "3"))


# ----------------- Utilities -----------------
def _set_perms(p: pathlib.Path) -> None:
    """確保檔案權限允許群組寫入，避免不同服務 user 無法更新。"""
    try:
        os.chmod(p, 0o664)
    except Exception:
        pass


def _log(line: str) -> None:
    """簡單寫 log 到 /home/da40/charter/var/pdu_mute.log。"""
    try:
        with LOG_FILE.open("a") as f:
            f.write(f"{datetime.datetime.now().isoformat()} {line}\n")
        _set_perms(LOG_FILE)
    except Exception:
        pass


def _now() -> float:
    return time.time()


def _read_until() -> float:
    """讀取目前 mute 截止時間（epoch 秒），沒有就回 0。"""
    try:
        s = MUTE_FILE.read_text().strip()
        if not s:
            return 0.0
        return float(s)
    except FileNotFoundError:
        return 0.0
    except Exception:
        return 0.0


def _clear_stale_mute(reason: str) -> bool:
    """
    只清「過期」的 serial.mute（stale cleanup）。
    - still-active (left > 0) 絕不清，避免干擾其他腳本。
    """
    try:
        if not MUTE_FILE.exists():
            return False
        until = _read_until()
        now = _now()
        if until <= 0 or until <= now:
            try:
                MUTE_FILE.unlink()
            except FileNotFoundError:
                return False
            except Exception:
                return False
            _log(f"mute_clear stale reason={reason} until={int(until)} now={int(now)}")
            return True
        return False
    except Exception:
        return False


def _spawn_autoclear(expected_until: float, grace_sec: int, reason: str) -> None:
    """
    在背景起一個短程序：等到到期 + grace 後，
    如果 serial.mute 內容仍等於 expected_until（允許 1 秒誤差），就刪掉。
    """
    if not MUTE_AUTOCLEAR:
        return
    try:
        delay = max(0.0, float(expected_until) - _now() + float(grace_sec))
        py = sys.executable or "python3"
        code = r"""
import os, sys, time
path = sys.argv[1]
exp = float(sys.argv[2])
delay = float(sys.argv[3])
time.sleep(max(0.0, delay))
try:
    with open(path, "r") as f:
        s = f.read().strip()
    cur = float(s) if s else 0.0
except Exception:
    cur = 0.0
# 只清「仍然是我當初設的那次」：允許 1 秒誤差
if cur and abs(cur - exp) < 1.0:
    try:
        os.remove(path)
    except Exception:
        pass
"""
        subprocess.Popen(
            [py, "-c", code, str(MUTE_FILE), str(float(expected_until)), str(float(delay))],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
            close_fds=True,
        )
        _log(f"spawn_autoclear reason={reason} exp_until={int(expected_until)} delay={int(delay)}")
    except Exception as e:
        _log(f"spawn_autoclear_failed reason={reason} err={e}")


def _mute_for(secs: int, reason: str) -> Tuple[float, bool]:
    """
    設定「從現在起靜默 secs 秒」，並寫入 serial.mute。

    - 若目前 mute_until 已經比新設定晚，就保留原本值（避免 race）。
    - 回傳 (until_ts, did_set)
    """
    secs = max(0, int(secs))
    target = _now() + secs
    current = _read_until()
    base = f"by_uid={os.geteuid()} path={os.path.abspath(__file__)} pid={os.getpid()} mute_secs={secs}"

    # 若原本就 mute 得比較久，就不縮短
    if current >= target - 1:
        _log(f"skip_set_mute reason={reason} keep_until={int(current)} {base}")
        return current, False

    # 寫入（整數 epoch 秒，避免浮點比對問題）
    until_i = int(target)
    try:
        MUTE_FILE.write_text(str(until_i))
        _set_perms(MUTE_FILE)
    except Exception as e:
        _log(f"set_mute_failed reason={reason} err={e} {base}")
        return current, False

    _log(f"set_mute={secs} reason={reason} until={until_i} {base}")
    return float(until_i), True


# ----------------- MSNSwitch/UIS HTTP helpers -----------------
def _base_url() -> str:
    return f"{PDU_PROTOCOL}://{PDU_IP}"


def _post(path: str, params: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    UIS API：POST form data 包含 user/password，回 JSON。
    """
    url = f"{_base_url()}{path}"
    payload: Dict[str, Any] = {"user": PDU_USER, "password": PDU_PASS}
    if data:
        payload.update(data)

    try:
        r = requests.post(url, params=params, data=payload, timeout=PDU_TIMEOUT, verify=PDU_VERIFY_SSL)
        if r.status_code in (401, 403):
            # 與舊版一致：權限錯要明顯
            raise RuntimeError(f"HTTP {r.status_code} auth denied: {r.text[:200]}")
        r.raise_for_status()
        return r.json()
    except Exception as e:
        raise RuntimeError(f"POST {url} failed: {e}") from e


def get_status() -> Dict[str, Any]:
    """讀取 UIS status，原樣回傳（其結構已符合 {'status': {'outlet': [...]}}）。"""
    return _post("/api/status")


def _extract_state_from_status(status_js: Dict[str, Any], outlet_id: int) -> Optional[bool]:
    """
    從 /api/status 回傳中找指定 outlet 狀態（best-effort）。
    預期格式：
      {"status":{"outlet":[{"status": true/false, ...}, ...]}}
    """
    try:
        outlets = status_js.get("status", {}).get("outlet", [])
        idx = max(0, int(outlet_id) - 1)
        if not isinstance(outlets, list) or idx >= len(outlets):
            return None
        item = outlets[idx]
        if isinstance(item, dict) and "status" in item:
            return bool(item.get("status"))
        # 萬一回傳是 bool/list 之類
        if isinstance(item, bool):
            return bool(item)
        return None
    except Exception:
        return None


def outlet_control(action: str, outlet_id: Optional[int] = None) -> Dict[str, Any]:
    """
    控制指定 outlet 的電源（action in {"on","off","reset"}）。
    回傳格式比照 pdu_outlet2.py，並向後相容提供 "outlet":[bool]。
    """
    action = (action or "").strip().lower()
    if action not in {"on", "off", "reset"}:
        raise ValueError(f"Unsupported action: {action}")

    if outlet_id is None:
        outlet_id = OUTLET_ID
    try:
        outlet_id_i = int(outlet_id)
    except Exception:
        outlet_id_i = 1
    if outlet_id_i < 1:
        raise ValueError("PDU_OUTLET_ID must be >= 1")

    _log(f"interp={sys.executable} ver={sys.version.split()[0]} action={action} outlet_id={outlet_id_i}")

    # 只清過期的殘留 mute（不影響 still-active）
    _clear_stale_mute(reason=f"pre:{action}")

    mute_set = False
    mute_until = 0
    mute_left = 0

    # ON/RESET 先靜默
    if action in ("on", "reset"):
        until, did_set = _mute_for(MUTE_SECS, reason=f"func:{action}")
        mute_set = bool(did_set)
        mute_until = int(until) if until else 0
        mute_left = max(0, int(mute_until - _now())) if mute_until else 0
        if did_set and mute_until > 0:
            _spawn_autoclear(expected_until=float(mute_until), grace_sec=MUTE_AUTOCLEAR_GRACE, reason=f"{action}")

    resp: Optional[Dict[str, Any]] = None
    status_js: Optional[Dict[str, Any]] = None
    err: Optional[str] = None
    ok = False
    state_bool = False

    try:
        target = f"outlet{outlet_id_i}"
        resp = _post("/api/control", params={"target": target, "action": action})
        ok = True
    except Exception as e:
        ok = False
        err = str(e)

    # 盡量用 status 決定 state（比 control 回應更穩）
    try:
        status_js = get_status()
        st = _extract_state_from_status(status_js, outlet_id_i)
        if st is not None:
            state_bool = bool(st)
        else:
            # fallback：如果 control 回應有 "outlet": [...]
            if isinstance(resp, dict):
                out = resp.get("outlet")
                if isinstance(out, list) and out:
                    state_bool = bool(out[0])
    except Exception as e:
        if err:
            err = f"{err}; status_failed: {e}"
        else:
            err = f"status_failed: {e}"

    # 統一回傳（向後相容）
    return {
        "ok": bool(ok),
        "outlet": [bool(state_bool)],
        "mute_set": bool(mute_set),
        "mute_until": int(mute_until),
        "mute_left_sec": int(mute_left),
        "resp": resp,
        "status": status_js,
        "error": err,
        "outlet_id": int(outlet_id_i),
    }


# 向後相容：舊腳本 import outlet1_control
def outlet1_control(action: str) -> Dict[str, Any]:
    return outlet_control(action, outlet_id=OUTLET_ID)


# ----------------- CLI entry -----------------
def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in {"on", "off", "reset", "status"}:
        print(f"用法: python {sys.argv[0]} [on|off|reset|status]")
        sys.exit(1)

    cmd = sys.argv[1]

    # CLI 一開始也做一次 stale cleanup（只清過期）
    _clear_stale_mute(reason=f"cli:{cmd}:start")

    if cmd == "status":
        try:
            js = get_status()
            st = _extract_state_from_status(js, OUTLET_ID)
            if st is None:
                raise RuntimeError("status parse failed")
            print(f"Outlet {OUTLET_ID} 目前狀態：{'ON' if st else 'OFF'}")
            sys.exit(0)
        except Exception as e:
            print(f"[ERROR] failed to get status from {PDU_BRAND}: {e}")
            sys.exit(2)

    js = outlet1_control(cmd)

    # mute log（比照 pdu_outlet2.py）
    if cmd in ("on", "reset"):
        if js.get("mute_set"):
            print(f"[序列靜默] {MUTE_SECS}s 已設定", flush=True)
        else:
            left = int(js.get("mute_left_sec", 0) or 0)
            if left > 0:
                print(f"[序列靜默] 已存在，剩餘 {left}s（不縮短）", flush=True)
            else:
                print(f"[序列靜默] 未設定（可能寫檔失敗或 secs=0）", flush=True)

    o_state = bool(js.get("outlet", [False])[0])
    if not js.get("ok", False):
        print(f"[ERROR] {PDU_BRAND} outlet{OUTLET_ID} {cmd.upper()} failed: {js.get('error')}")
        print(f"Outlet {OUTLET_ID} 新狀態：{'ON' if o_state else 'OFF'}")
        sys.exit(2)

    print(f"已執行 outlet{OUTLET_ID} {cmd.upper()}，Outlet {OUTLET_ID} 新狀態：{'ON' if o_state else 'OFF'}")
    sys.exit(0)


if __name__ == "__main__":
    main()

