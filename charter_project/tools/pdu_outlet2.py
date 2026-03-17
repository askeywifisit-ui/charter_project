#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
pdu_outlet2: Control customer's WEBPOWERSWITCH.COM (DLI Web Power Switch)
（含全域序列靜默，行為比照 pdu_outlet1.py：stale 清理 + 設定後自動清除）

CLI:
    python3 pdu_outlet2.py on
    python3 pdu_outlet2.py off
    python3 pdu_outlet2.py reset
    python3 pdu_outlet2.py status

API:
    from pdu_outlet2 import outlet1_control, get_status
    outlet1_control("on" / "off" / "reset")
    get_status()

環境變數：
    PDU_IP                 預設 "192.168.168.61"
    PDU_USER               預設 "admin"
    PDU_PASS               預設 "1234"
    PDU_OUTLET_ID          預設 "1"
    PDU_MUTE_SECS          預設 70（ON/RESET 會先靜默 N 秒）
    PDU_MUTE_AUTOCLEAR     預設 1（啟用：到期後自動 clear 自己設定的 serial.mute）
    PDU_MUTE_AUTOCLEAR_GRACE 預設 3（到期後多等 N 秒再嘗試清除，避免 race）
"""

import sys
import os
import time
import datetime
import pathlib
import re
import subprocess
from typing import Dict, Any, Tuple

import requests


# ===== 依現場調整（可被環境變數覆蓋） =====
PDU_BRAND = "WEBPOWERSWITCH.COM"
PDU_IP = os.getenv("PDU_IP", "192.168.168.61")
PDU_USER = os.getenv("PDU_USER", "admin")
PDU_PASS = os.getenv("PDU_PASS", "1234")
OUTLET_ID = os.getenv("PDU_OUTLET_ID", "1")  # DLI outlet index, e.g., "1"
REQUEST_TIMEOUT = 6
# ======================================

# ---- 路徑 / 旗標檔（比照 pdu_outlet1.py）----
VAR_DIR = pathlib.Path("/home/da40/charter/var")
VAR_DIR.mkdir(parents=True, exist_ok=True)
MUTE_FILE = VAR_DIR / "serial.mute"
LOG_FILE = VAR_DIR / "pdu_mute.log"
MUTE_SECS = int(os.getenv("PDU_MUTE_SECS", "70"))

MUTE_AUTOCLEAR = os.getenv("PDU_MUTE_AUTOCLEAR", "1").strip().lower() not in ("0", "false", "no", "off")
MUTE_AUTOCLEAR_GRACE = int(os.getenv("PDU_MUTE_AUTOCLEAR_GRACE", "3"))


def _set_perms(p: pathlib.Path) -> None:
    """確保檔案權限允許群組寫入，避免不同服務 user 無法更新。"""
    try:
        os.chmod(p, 0o664)
    except Exception:
        # 權限調整失敗不算致命，不要讓主流程炸掉
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
        # 壞檔：當作 0（不主動刪除，避免誤清）
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
        # active，不清
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
    base = (
        f"by_uid={os.geteuid()} path={os.path.abspath(__file__)} "
        f"pid={os.getpid()} mute_secs={secs}"
    )

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


# ---- DLI HTTP helpers ----
def _base_url() -> str:
    return f"http://{PDU_IP}"


def _status_url() -> str:
    # DLI Web Power Switch 預設首頁
    return f"{_base_url()}/index.htm"


def _control_url(command: str) -> str:
    """
    DLI 控制定義：
      /outlet?{OUTLET_ID}=ON|OFF|CCL
    其中 CCL = cycle（off → on）
    """
    return f"{_base_url()}/outlet?{OUTLET_ID}={command}"


def _send_power_command(command: str) -> bool:
    """
    真正送出 DLI 控制命令。
    command = "ON" / "OFF" / "CCL"
    """
    actual_command = "CYCLE" if command == "CCL" else command
    url = _control_url(command)

    try:
        resp = requests.get(url, auth=(PDU_USER, PDU_PASS), timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        print(f"[INFO] {PDU_BRAND} outlet{OUTLET_ID} {actual_command} sent OK")
        return True
    except Exception as e:
        print(f"[ERROR] {PDU_BRAND} outlet{OUTLET_ID} {actual_command} failed: {e}")
        return False


def _strip_html_tags(text: str) -> str:
    # 簡單移除 HTML tag，用於從 table 抓 ON/OFF 文字
    return re.sub(r"<.*?>", "", text)


def _parse_status_html(html: str) -> Dict[str, Any]:
    """
    解析 DLI status 頁面，回傳統一 JSON 介面：

    {
        "status": {
            "outlet": [
                {"id": 1, "status": True},
                {"id": 2, "status": False},
                ...
            ]
        }
    }

    備註：不同韌體 HTML 格式可能略有不同，
         這裡是「best-effort」簡易解析；若抓不到，就標記為 False。
    """
    outlets = []

    row_pattern = re.compile(
        r"<tr[^>]*>\s*"
        r"(?:<td[^>]*>.*?</td>\s*){0,1}"
        r"<td[^>]*>\s*(\d+)\s*</td>\s*"
        r"(?:<td[^>]*>.*?</td>\s*){0,2}"
        r"<td[^>]*>\s*(ON|OFF)\s*</td>",
        re.IGNORECASE | re.DOTALL,
    )

    for m in row_pattern.finditer(html):
        outlet_id = int(m.group(1))
        state_str = m.group(2).strip().upper()
        state_bool = state_str == "ON"
        outlets.append({"id": outlet_id, "status": state_bool})

    if not outlets:
        try:
            oid = int(OUTLET_ID)
        except ValueError:
            oid = 1
        outlets.append({"id": oid, "status": False})

    return {"status": {"outlet": outlets}}


def get_status() -> Dict[str, Any]:
    """讀取 DLI status 頁面並回傳統一 JSON 格式。"""
    try:
        resp = requests.get(_status_url(), auth=(PDU_USER, PDU_PASS), timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        html = resp.text
        js = _parse_status_html(html)
        return js
    except Exception as e:
        print(f"[ERROR] failed to get status from {PDU_BRAND}: {e}")
        try:
            oid = int(OUTLET_ID)
        except ValueError:
            oid = 1
        return {"status": {"outlet": [{"id": oid, "status": False}]}}


# ---- 對外 API（給其他腳本 / Web GUI 用）----
def outlet1_control(action: str) -> Dict[str, Any]:
    """
    控制指定 OUTLET_ID 的電源：
      action in {"on", "off", "reset"}

    回傳 JSON（向後相容，額外補欄位不影響舊呼叫端）：
      {"ok": ok, "outlet": [state_bool], "mute_set": bool, "mute_until": int, "mute_left_sec": int}
    """
    action = action.lower()
    if action not in {"on", "off", "reset"}:
        raise ValueError(f"Unsupported action: {action}")

    _log(f"interp={sys.executable} ver={sys.version.split()[0]} action={action}")

    # 先清過期的殘留 mute（不影響 still-active）
    _clear_stale_mute(reason=f"pre:{action}")

    mute_set = False
    mute_until = 0
    mute_left = 0

    if action in ("on", "reset"):
        until, did_set = _mute_for(MUTE_SECS, reason=f"func:{action}")
        mute_set = bool(did_set)
        mute_until = int(until) if until else 0
        mute_left = max(0, int(mute_until - _now())) if mute_until else 0
        # 只在「我確實 set 成功」時才 spawn autoclear
        if did_set and mute_until > 0:
            _spawn_autoclear(expected_until=float(mute_until), grace_sec=MUTE_AUTOCLEAR_GRACE, reason=f"{action}")

    if action == "on":
        ok = _send_power_command("ON")
    elif action == "off":
        ok = _send_power_command("OFF")
    else:
        ok = _send_power_command("CCL")

    js_status = get_status()
    outlets = js_status.get("status", {}).get("outlet", [])

    try:
        oid = int(OUTLET_ID)
    except ValueError:
        oid = 1

    state_bool = False
    for o in outlets:
        if int(o.get("id", 0)) == oid:
            state_bool = bool(o.get("status"))
            break

    return {
        "ok": ok,
        "outlet": [state_bool],
        "mute_set": mute_set,
        "mute_until": mute_until,
        "mute_left_sec": mute_left,
    }


# ---- CLI 入口 ----
def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in {"on", "off", "reset", "status"}:
        print(f"用法: python {sys.argv[0]} [on|off|reset|status]")
        sys.exit(1)

    cmd = sys.argv[1]

    # CLI 一開始也做一次 stale cleanup（只清過期）
    _clear_stale_mute(reason=f"cli:{cmd}:start")

    if cmd == "status":
        js = get_status()
        outlets = js["status"]["outlet"]
        try:
            oid = int(OUTLET_ID)
        except ValueError:
            oid = 1

        state_bool = False
        for o in outlets:
            if int(o.get("id", 0)) == oid:
                state_bool = bool(o.get("status"))
                break

        print(f"Outlet {OUTLET_ID} 目前狀態：{'ON' if state_bool else 'OFF'}")
        return

    js = outlet1_control(cmd)

    if cmd in ("on", "reset"):
        if js.get("mute_set"):
            print(f"[序列靜默] {MUTE_SECS}s 已設定", flush=True)
        else:
            left = int(js.get("mute_left_sec", 0) or 0)
            if left > 0:
                print(f"[序列靜默] 已存在，剩餘 {left}s（不縮短）", flush=True)
            else:
                print(f"[序列靜默] 未設定（可能寫檔失敗或 secs=0）", flush=True)

    o1_state = js["outlet"][0]
    print(
        f"已執行 outlet{OUTLET_ID} {cmd.upper()}，Outlet {OUTLET_ID} 新狀態："
        f"{'ON' if o1_state else 'OFF'}"
    )


if __name__ == "__main__":
    main()

