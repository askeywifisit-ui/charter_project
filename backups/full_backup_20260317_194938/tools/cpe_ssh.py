#!/usr/bin/env python3
# --- worker-only pull-log hard guard (inserted) ---
import os as __os_guard, json as __json_guard, sys as __sys_guard
try:
    __argv_low = " ".join(__sys_guard.argv).lower()
    if ("--cmd" in __argv_low and "pull-log" in __argv_low) or " pull-log " in __argv_low:
        __worker_ok = str(__os_guard.environ.get("WORKER_PULL","0")).lower() in ("1","true","yes")
        __script_ok = str(__os_guard.environ.get("SCRIPT_LOGPULL","0")).lower() in ("1","true","yes")
        if not (__worker_ok or __script_ok):
            try:
                print(__json_guard.dumps({"step":"logpull-trigger","reason":"blocked-by-worker-only"},
                                         ensure_ascii=False, separators=(",",":")))
            except Exception:
                pass
            # Exit quietly as success to not break flows
            raise SystemExit(0)
except SystemExit:
    raise
except Exception:
    pass
# --- end hard guard ---
# -*- coding: utf-8 -*-
"""
cpe_ssh.py — SSH helper for querying AWLAN_Node.id, safe reboot (with console mute),
and pulling logs via scp only (NO SFTP).

新增：
  - --delete-remote：下載成功後自動刪除遠端原檔（預設關閉）
  - 預設靜音 ssh/scp（LogLevel=ERROR），可用 --no-ssh-quiet 關閉
  - 下載後自動以 node-id 前綴重新命名（預設開），可用 --no-rename-with-node-id 關閉

功能摘要：
  - node-id: 透過 ovsh 取得 AWLAN_Node.id（含 root fallback）
  - reboot : 觸發重開機，可選擇先設定 serial console mute（支援 lock）
  - pull-log: 以 scp 從 CPE 拉回 logs
      (預設) 下載前先執行 /usr/opensync/scripts/logpull/logpull.sh --local
      (A) --latest-from-dir <DIR> [--pattern "*.tar.gz"]：挑遠端目錄中 mtime 最新檔
      (B) --src <PATH> [--src <PATH> ...]：直接拉指定/萬用字元路徑
          ※ 萬用字元由「先 ssh 展開 → 再逐一 scp」處理
          ※ 自動忽略遠端 shell 的 banner/ANSI 顏色碼，只保留符合 pattern 的檔名行
"""

import os
import re
import fnmatch
import time
import json
import shlex
import argparse
import contextlib
import subprocess
import shutil
import ipaddress
import datetime
import calendar

# ---------- defaults ----------
DEFAULT_TIMEOUT = float(os.environ.get("SSH_TIMEOUT_SEC", "10"))
LOGIN_SHELL = os.environ.get("SSH_LOGIN_SHELL", "sh -lc").strip()
DEFAULT_LOGPULL_DIR = os.environ.get("LOGPULL_DEFAULT_DIR", "/tmp/logpull")
DEFAULT_LOGPULL_PATTERN = os.environ.get("LOGPULL_PATTERN", "*.tar.gz")
DEFAULT_LOCAL_DEST = os.environ.get("LOGPULL_DEST", "/home/da40/charter/logs/cpe")
DEFAULT_PRE_LOGPULL_TIMEOUT = int(os.environ.get("LOGPULL_PRE_TIMEOUT_SEC", "90"))
_SSH_LOGLEVEL = os.environ.get("SSH_LOGLEVEL", "ERROR")

# ---------- optional deps ----------
try:
    from serial_lock import acquire as serial_lock_acquire  # context manager
except Exception:
    serial_lock_acquire = None

try:
    import serial_mute
except Exception:
    serial_mute = None

# ---------- helpers ----------
ANSI_RE = re.compile(r"\x1B\[[0-9;?]*[ -/]*[@-~]")

def _strip_ansi(s: str) -> str:
    return ANSI_RE.sub("", s or "").replace("\r", "")

# ---------- Wi-Fi credentials helpers ----------
_MF_TOOL_KV_RE = re.compile(r'^\s*([A-Za-z0-9_]+)\s*:\s*\[([^\]]*)\]\s*$')


def _parse_mf_tool_show(text: str) -> dict:
    """Parse `mf_tool show` output into a key/value dict."""
    raw = _strip_ansi(text or "")
    out: dict = {}
    for line in raw.splitlines():
        m = _MF_TOOL_KV_RE.match(line)
        if not m:
            continue
        k = m.group(1).strip()
        v = m.group(2).strip()
        out[k] = v
    return out


def _extract_psk_from_wpa_psks(val: str):
    """Extract PSK from ovsh wpa_psks field, tolerating key-1 / key--1 formats."""
    if not val:
        return None
    s = str(val).strip()
    if s in ("[]", "null", "None"):
        return None
    # Try JSON first
    try:
        obj = __import__('json').loads(s)
        if isinstance(obj, list) and len(obj) >= 2 and obj[0] == "map":
            pairs = obj[1]
            if isinstance(pairs, list):
                for pair in pairs:
                    if not isinstance(pair, list) or len(pair) < 2:
                        continue
                    k, v = pair[0], pair[1]
                    k_norm = re.sub(r'[^A-Za-z0-9]', '', str(k)).lower()
                    if k_norm == 'key1':
                        return str(v)
                # fallback: first pair's value
                if pairs and isinstance(pairs[0], list) and len(pairs[0]) >= 2:
                    return str(pairs[0][1])
        if isinstance(obj, str):
            return obj
    except Exception:
        pass
    # Fallback: last quoted string
    m = re.findall(r'"([^"]+)"', s)
    return m[-1] if m else None


def _parse_ovsh_wifi_vif_config(text: str) -> list[dict]:
    """Parse ovsh Wifi_VIF_Config output into rows with keys: if_name, ssid, wpa_psks."""
    raw = _strip_ansi(text or "")
    rows: list[dict] = []
    cur: dict = {}

    def _flush():
        nonlocal cur
        if cur:
            rows.append(cur)
            cur = {}

    for line in raw.splitlines():
        l = line.strip()
        if not l:
            continue
        # record separator lines are often all dashes
        if l and set(l) == {'-'}:
            _flush()
            continue
        # colon style: key : value
        m = re.match(r'^([A-Za-z0-9_]+)\s*:\s*(.*)$', l)
        if m:
            k = m.group(1).strip()
            v = m.group(2).strip()
            if k in ('if_name', 'ssid', 'wpa_psks'):
                if k == 'if_name' and 'if_name' in cur:
                    _flush()
                cur[k] = v
            continue
        # pipe style table (rare): | if_name | ssid | wpa_psks |
        if '|' in l:
            parts=[p.strip() for p in l.split('|') if p.strip()]
            if len(parts)==2 and parts[0] in ('if_name','ssid','wpa_psks'):
                k,v=parts
                if k=='if_name' and 'if_name' in cur:
                    _flush()
                cur[k]=v

    _flush()
    # If we parsed nothing, try a simple key|value scan without separators
    if not rows:
        cur={}
        for line in raw.splitlines():
            l=line.strip()
            if not l:
                continue
            if '|' not in l:
                continue
            parts=[p.strip() for p in l.split('|') if p.strip()]
            if len(parts)!=2:
                continue
            k,v=parts
            if k not in ('if_name','ssid','wpa_psks'):
                continue
            if k=='if_name' and cur:
                rows.append(cur); cur={}
            cur[k]=v
        if cur:
            rows.append(cur)
    return rows

def _env_any(names, default=None):
    for n in names:
        v = os.environ.get(n)
        if v not in (None, ""):
            return v
    return default

def _sshpass_ok():
    return shutil.which("sshpass") is not None

def _dq(s: str) -> str:
    return (s or "").replace("\\", "\\\\").replace('"', '\\"')

def _shell_quote_single(s: str) -> str:
    return "'" + (s or "").replace("'", "'\"'\"'") + "'"

def _has_glob(s: str) -> bool:
    return any(c in s for c in "*?[")

def _filter_paths(text: str, *, directory: str, pattern: str) -> list[str]:
    lines = [l.strip() for l in (text or "").splitlines() if l.strip()]
    directory = directory.rstrip("/")
    res: list[str] = []
    for l in lines:
        b = os.path.basename(l)
        if fnmatch.fnmatch(b, pattern):
            if directory:
                res.append(f"{directory}/{b}")
            else:
                res.append(b)
    return res

# ---------- SSH core ----------
def ssh_exec(host, user, password, cmd, *, timeout=DEFAULT_TIMEOUT, login_shell=True, bind_src=None):
    """
    Execute remote command via system ssh (optionally through sshpass).

    Args:
      host, user, password: ssh target and credential
      cmd: remote command string
      timeout: subprocess timeout (seconds)
      login_shell: if True, wrap with LOGIN_SHELL
      bind_src: optional source IP to bind (ssh -b <bind_src>), default None (no -b)

    Returns:
      (rc, out, err, sec)
    """
    t0 = time.time()
    use_sshpass = bool(password) and _sshpass_ok()
    bind_src = bind_src or os.environ.get("SSH_BIND_SRC")
    base = [
        "ssh",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "StrictHostKeyChecking=no",
        "-o", f"LogLevel={_SSH_LOGLEVEL}",
    ]

    # ✅ optional bind source IP (no impact if bind_src is None/empty)
    if bind_src:
        base += ["-b", str(bind_src)]

    if not use_sshpass:
        base += ["-o", "BatchMode=yes"]

    base += [f"{user}@{host}"]

    remote = f'{LOGIN_SHELL} "{_dq(cmd)}"' if login_shell else cmd
    full = base + [remote]

    if use_sshpass:
        full = ["sshpass", "-p", password] + full

    try:
        p = subprocess.run(
            full,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout
        )
        rc, out, err = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        rc, out, err = 124, "", f"ssh timeout after {timeout}s"
    except Exception as e:
        rc, out, err = 255, "", f"{type(e).__name__}: {e}"

    sec = round(time.time() - t0, 3)
    return rc, out, err, sec

def _scp_download(host: str, user: str, password: str, remote_path: str, local_path: str,
                  timeout: float = DEFAULT_TIMEOUT, recursive: bool = False):
    t0 = time.time()
    use_sshpass = bool(password) and _sshpass_ok()
    cmd = ["scp",
           "-o", "UserKnownHostsFile=/dev/null",
           "-o", "StrictHostKeyChecking=no",
           "-o", f"LogLevel={_SSH_LOGLEVEL}"]
    bind_src = os.environ.get("SSH_BIND_SRC")
    if bind_src:
        cmd += ["-o", f"BindAddress={bind_src}"]
    if not use_sshpass:
        cmd += ["-o", "BatchMode=yes"]
    if recursive:
        cmd.append("-r")
    cmd += [f"{user}@{host}:{remote_path}", local_path]
    if use_sshpass:
        cmd = ["sshpass", "-p", password] + cmd
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
        rc, out, err = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        rc, out, err = 124, "", f"scp timeout after {timeout}s"
    except Exception as e:
        rc, out, err = 255, "", f"{type(e).__name__}: {e}"
    sec = round(time.time() - t0, 3)
    return rc, out, err, sec

# ---------- AWLAN node-id ----------
OVSH_CHAIN = (
    "([ -x /usr/opensync/tools/ovsh ] && /usr/opensync/tools/ovsh {args})"
    " || "
    "([ -x /usr/opensync/bin/ovsh ] && /usr/opensync/bin/ovsh {args})"
    " || "
    "(ovsh {args})"
)
ID_PAT = re.compile(r'\b([0-9a-f]{10,})\b', re.I)

def _parse_node_id(text: str) -> str:
    for line in (text or ""):
        pass
    for line in (text or "").splitlines():
        m = re.search(r'\bid\s*[:=]\s*([0-9a-f]{10,})\b', line, re.I)
        if m:
            return m.group(1).lower()
    m = ID_PAT.search(text or "")
    return m.group(1).lower() if m else (text or "").strip()

def get_awlan_node_id(host: str, *, user: str = None, password: str = None,
                      root_fallback: bool = True, timeout: float = DEFAULT_TIMEOUT):
    user = user or _env_any(["SSH_USER", "SSH_USERNAME", "OPERATOR_USER"], "operator")
    password = password or _env_any(["SSH_PASSWORD", "PASSWORD", "CPE_PASSWORD"], "")
    root_user = os.environ.get("SSH_USER_LAN_FALLBACK", "root")
    root_pass = _env_any(["CPE_PASSWORD", "CPE_PASS", "SSH_ROOT_PASSWORD"], password)
    attempts, cmds = [], [
        OVSH_CHAIN.format(args="s -r AWLAN_Node -c id 2>/dev/null"),
        OVSH_CHAIN.format(args="s AWLAN_Node id 2>/dev/null"),
    ]
    for cmd in cmds:
        rc, out, err, sec = ssh_exec(host, user, password, cmd, timeout=timeout, login_shell=True)
        attempts.append({"user": user, "cmd": cmd, "rc": rc, "sec": sec, "out": (out or "")[:200].strip(), "err": (err or "")[:200].strip()})
        nid = _parse_node_id((out or "") + "\n" + (err or ""))
        if nid:
            return nid, {"ok": True, "user": user, "rc": rc, "sec": sec, "cmd": cmd, "out": out, "err": err, "attempts": attempts}
    if root_fallback and user != root_user:
        for cmd in cmds:
            rc, out, err, sec = ssh_exec(host, root_user, root_pass, cmd, timeout=timeout, login_shell=True)
            attempts.append({"user": root_user, "cmd": cmd, "rc": rc, "sec": sec, "out": (out or "")[:200].strip(), "err": (err or "")[:200].strip()})
            nid = _parse_node_id((out or "") + "\n" + (err or ""))
            if nid:
                return nid, {"ok": True, "user": root_user, "rc": rc, "sec": sec, "cmd": cmd, "out": out, "err": err, "attempts": attempts}
    last = attempts[-1] if attempts else {}
    return None, {"ok": False, "user": last.get("user"), "rc": last.get("rc"), "sec": last.get("sec"),
                   "cmd": last.get("cmd"), "out": last.get("out"), "err": last.get("err"), "attempts": attempts}


# ---------- AWLAN node info (serial/model/firmware) ----------
_AWLAN_TABLE_KV_RE = re.compile(r'^\s*([A-Za-z0-9_]+)\s*\|\s*([^|]*?)\s*\|.*$')

def _parse_awlan_node_table(text: str) -> dict:
    """Parse `ovsh s AWLAN_Node` table output.

    Robust to extra columns and trailing '|' separators.
    Returns dict of parsed keys/values (best-effort).
    """
    raw = _strip_ansi(text or "")
    out: dict = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        # Skip table separators
        if line.startswith("---") or set(line) <= set("-+|"):
            continue

        # ovsh table lines look like: key | value | ...
        if "|" not in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 2:
            continue
        k = parts[0]
        v = parts[1]
        if not k:
            continue
        out[k] = v
    return out

def get_awlan_node_info(host: str, *, user: str = None, password: str = None,
                        root_fallback: bool = True, timeout: float = DEFAULT_TIMEOUT):
    """
    One-shot capture from CPE via SSH:
      - AWLAN_Node.serial_number
      - AWLAN_Node.model
      - AWLAN_Node.firmware_version

    Returns:
      (info_dict, meta)

    Notes:
      - Uses a single SSH command (`ovsh s AWLAN_Node`) and parses the table output.
      - Includes root fallback (same behavior as get_awlan_node_id()).
    """
    user = user or _env_any(["SSH_USER", "SSH_USERNAME", "OPERATOR_USER"], "operator")
    password = password or _env_any(["SSH_PASSWORD", "PASSWORD", "CPE_PASSWORD"], "")
    root_user = os.environ.get("SSH_USER_LAN_FALLBACK", "root")
    root_pass = _env_any(["CPE_PASSWORD", "CPE_PASS", "SSH_ROOT_PASSWORD"], password)

    attempts = []
    cmd = OVSH_CHAIN.format(args="s AWLAN_Node 2>/dev/null")

    def _run(u: str, pw: str):
        rc, out, err, sec = ssh_exec(host, u, pw, cmd, timeout=timeout, login_shell=True)
        text_all = (out or "") + "\n" + (err or "")
        kv = _parse_awlan_node_table(text_all)

        info = {
            "serial_number": kv.get("serial_number") or None,
            "model": kv.get("model") or None,
            "firmware_version": kv.get("firmware_version") or None,
        }

        ok = bool(info["serial_number"] and info["model"] and info["firmware_version"])

        attempts.append({
            "user": u,
            "cmd": cmd,
            "rc": rc,
            "sec": sec,
            "serial_number": (info["serial_number"] or "")[:64],
            "model": (info["model"] or "")[:64],
            "firmware_version": (info["firmware_version"] or "")[:128],
            "err": (_strip_ansi(err or "") or "")[:200],
        })

        meta = {
            "ok": ok,
            "host": host,
            "user": u,
            "rc": rc,
            "sec": sec,
            "cmd": cmd,
            "stderr": _strip_ansi(err or "")[-300:],
            "attempts": attempts,
        }
        return info, meta

    # Try operator first, then optional root fallback.
    info, meta = _run(user, password)
    if meta.get("ok"):
        return info, meta

    if root_fallback and user != root_user and root_user:
        info2, meta2 = _run(root_user, root_pass)
        return info2, meta2

    return {"serial_number": None, "model": None, "firmware_version": None}, meta

# ---------- reboot（補回來） ----------
def trigger_reboot(host: str, *, user: str = None, password: str = None,
                   root_fallback: bool = True, timeout: float = DEFAULT_TIMEOUT):
    """
    透過 SSH 送 reboot 指令。
    成功時回傳 (True, meta)，失敗回傳 (False, meta)。
    CLI 模式下，成功只會印出 'REBOOTING'（這跟你原本的使用方式一致）。
    """
    user = user or _env_any(["SSH_USER", "SSH_USERNAME", "OPERATOR_USER"], "operator")
    password = password or _env_any(["SSH_PASSWORD", "PASSWORD", "CPE_PASSWORD"], "")
    root_user = os.environ.get("SSH_USER_LAN_FALLBACK", "root")
    root_pass = _env_any(["CPE_PASSWORD", "CPE_PASS", "SSH_ROOT_PASSWORD"], password)

    attempts = []
    cmds = []

    # 先試 root，再試 operator（和原本邏輯一致）
    if root_fallback and root_user:
        cmds.append((root_user, root_pass, "reboot || /sbin/reboot || true"))
    cmds.append((user, password, "reboot || /sbin/reboot || true"))

    for u, pw, cmd in cmds:
        rc, out, err, sec = ssh_exec(host, u, pw, cmd, timeout=timeout, login_shell=True)
        attempts.append({
            "user": u,
            "cmd": cmd,
            "rc": rc,
            "sec": sec,
            "out": (out or "")[:200].strip(),
            "err": (err or "")[:200].strip(),
        })
        # 成功或連線斷掉都視為有送出 reboot
        if rc == 0 or "Connection to" in (err or ""):
            return True, {"ok": True, "attempts": attempts}

    return False, {"ok": False, "attempts": attempts}
    
# ---------- cpe uptime  ------------------#
def get_cpe_uptime(host: str,
                   user: str | None = None,
                   password: str | None = None,
                   timeout: float = DEFAULT_TIMEOUT) -> tuple[str | None, dict]:
    """
    透過 SSH 執行 `uptime`，回傳類似 "22 min" 或 "13:38" 的短字串。

    回傳:
      (value, meta)
        - value: 解析成功時為 "22 min"/"13:38"...，失敗為 None
        - meta : 附帶 rc/sec/stdout/stderr 等資訊，方便 debug
    """
    user = user or _env_any(["SSH_USER", "SSH_USERNAME", "OPERATOR_USER"], "operator")
    password = password or _env_any(["SSH_PASSWORD", "PASSWORD", "CPE_PASSWORD"], "")

    rc, out, err, sec = ssh_exec(
        host, user, password,
        "uptime",
        timeout=timeout,
        login_shell=True,
    )

    text = _strip_ansi((out or "") + " " + (err or ""))
    # 只抓 "up ...," 中間這段
    m = re.search(r"\bup\s+([^,]+),", text)
    value = m.group(1).strip() if m else None

    meta = {
        "ok": (rc == 0 and value is not None),
        "host": host,
        "user": user,
        "rc": rc,
        "sec": sec,
        "raw": text.strip(),
        "uptime": value,
        "stderr": _strip_ansi(err or "")[-200:],
    }
    return value, meta


# ---------- UPNP helpers (miniupnpd process & logcheck) ----------

# Many firmwares print SSH login banners (ASCII art/MOTD) even for non-interactive commands.
# For automation stability, we filter banner/ANSI and keep only meaningful lines.

UPNP_PROC_RE = re.compile(r"\bminiupnp(d)?\b", re.I)
_SYSLOG_TS_RE = re.compile(r'^([A-Z][a-z]{2})\s+(\d{1,2})\s+(\d{2}:\d{2}:\d{2})\s+')

def _filter_upnp_ps_lines(out_text: str) -> tuple[list[str], bool]:
    raw = _strip_ansi(out_text or "")
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    keep = [l for l in lines if UPNP_PROC_RE.search(l) and "grep" not in l.lower()]
    banner_present = bool(lines and (len(keep) != len(lines)))
    # de-dup keep order
    _seen = set()
    _tmp: list[str] = []
    for _l in keep:
        if _l in _seen:
            continue
        _seen.add(_l)
        _tmp.append(_l)
    return _tmp, banner_present

def _extract_pid_and_proc(line: str) -> tuple[int | None, str | None]:
    """
    Try to extract PID and command-ish string from a process line.
    Works for pgrep -af output and common ps outputs.
    """
    if not line:
        return None, None
    m = re.match(r"^\s*(\d+)\s+(.*)$", line)
    pid = int(m.group(1)) if m else None
    # best-effort command: take substring starting at 'miniupnp...'
    m2 = UPNP_PROC_RE.search(line)
    proc = line[m2.start():].strip() if m2 else None
    if proc and proc.lower().startswith("miniupnp"):
        # may be like 'miniupnpd ...' without path; that's fine
        return pid, proc
    return pid, proc

def check_upnp_process(host: str,
                       user: str | None = None,
                       password: str | None = None,
                       timeout: float = DEFAULT_TIMEOUT,
                       expect_found: int | None = None) -> tuple[int, dict]:
    """
    檢查 CPE 上 miniupnpd process 狀態（pgrep 優先，ps fallback）。

    回傳：
      (count, meta)
        - meta["ok"]   : SSH/指令層成功（可解析出結果）
        - meta["pass"] : 驗證是否符合 test plan 期望（由 expect_found 決定；未提供則等同 found）
        - meta["found"]/meta["running"] : 是否找到 miniupnpd
        - meta["pids"]/meta["procs"] : 方便腳本做更精準判斷
    """
    user = user or _env_any(["SSH_USER", "SSH_USERNAME", "OPERATOR_USER"], "operator")
    password = password or _env_any(["SSH_PASSWORD", "PASSWORD", "CPE_PASSWORD"], "")

    # If caller didn't override timeout (still DEFAULT_TIMEOUT), use a more forgiving default for upnp checks.
    env_timeout = os.environ.get("UPNP_SSH_TIMEOUT_SEC")
    if env_timeout:
        eff_timeout = float(env_timeout)
    else:
        eff_timeout = 30.0 if float(timeout) == float(DEFAULT_TIMEOUT) else float(timeout)

    retries = int(os.environ.get("UPNP_SSH_RETRIES", "5"))
    interval = float(os.environ.get("UPNP_SSH_RETRY_INTERVAL_SEC", "2"))

    # Prefer pgrep (lighter than ps) but keep a ps fallback.
    cmd = "(pgrep -af miniupnpd 2>/dev/null || pgrep -af miniupnp 2>/dev/null || true); ps w | grep -i miniupnp | grep -v grep || true"

    last = {"rc": 255, "out": "", "err": "", "sec": 0.0}
    for attempt in range(1, retries + 1):
        rc, out, err, sec = ssh_exec(host, user, password, cmd, timeout=eff_timeout, login_shell=True)
        last = {"rc": rc, "out": out, "err": err, "sec": sec}
        # rc 0/1 => command ran (1 might mean no match); 124/255 => timeout/ssh failure => retry
        if rc in (0, 1):
            break
        time.sleep(interval)

    lines, banner_present = _filter_upnp_ps_lines(last["out"])
    ok = last["rc"] in (0, 1)
    found = bool(lines)

    pids: list[int] = []
    procs: list[str] = []
    for l in lines:
        pid, proc = _extract_pid_and_proc(l)
        if pid is not None and pid not in pids:
            pids.append(pid)
        if proc and proc not in procs:
            procs.append(proc)

    # pass logic: if caller specified expect_found (0/1), compare; else default to "found"
    exp = None
    if expect_found is not None:
        exp = bool(int(expect_found))
        passed = ok and (found == exp)
    else:
        passed = ok and found

    count = len(lines)
    meta = {
        "ok": bool(ok),
        "pass": bool(passed),
        "host": host,
        "user": user,
        "rc": last["rc"],
        "sec": last["sec"],
        "timeout": eff_timeout,
        "retries": retries,
        "count": count,
        "found": found,
        "running": found,  # backward compatible alias
        "expect_found": exp,
        "pids": pids,
        "procs": procs,
        "lines": lines,
        "banner_present": banner_present,
        # backward compatible fields
        "stdout": f"{count}\n",
        "stderr": _strip_ansi(last["err"] or "")[-200:],
        "err": (_strip_ansi(last["err"]) or "").strip()[:400],
        "cmd": cmd,
    }
    return count, meta


import datetime as _dt
import re as _re

def _parse_syslog_time(line: str, now: _dt.datetime | None = None) -> _dt.datetime | None:
    """
    從一行 syslog 文字裡抓出 timestamp，轉成 datetime。
    抓不到就回傳 None。
    """
    m = _SYSLOG_TS_RE.match(line or "")
    if not m:
        return None
    month_name, day_str, time_str = m.groups()
    if now is None:
        now = _dt.datetime.utcnow()
    year = now.year
    try:
        dt = _dt.datetime.strptime(
            f"{year} {month_name} {day_str} {time_str}",
            "%Y %b %d %H:%M:%S",
        )
    except ValueError:
        return None

    # 處理跨年邊界：如果解析出來的時間比「現在多超過 1 天」，當成去年的
    if dt - now > _dt.timedelta(days=1):
        dt = dt.replace(year=year - 1)
    return dt


def check_upnp_logs(host: str,
                    user: str | None = None,
                    password: str | None = None,
                    timeout: float = DEFAULT_TIMEOUT,
                    log_file: str | None = None,
                    tail_lines: int = 200,
                    grep_word: str = "upnp",
                    window_min: int | None = None) -> dict:
    """
    檢查「最近一段時間」的 UPNP 相關 log（符合 test plan: log 裡不應有 UPNP error/fail/fatal/panic）。

    回傳 meta：
      - ok   : SSH/指令層成功
      - pass : 驗證通過（在時間窗內 bad_keywords 為空；若 log file 不存在則 pass=false）
    """
    user = user or _env_any(["SSH_USER", "SSH_USERNAME", "OPERATOR_USER"], "operator")
    password = password or _env_any(["SSH_PASSWORD", "PASSWORD", "CPE_PASSWORD"], "")
    log_file = log_file or os.environ.get("UPNP_LOG_FILE", "/var/log/messages")
    tail_lines = int(tail_lines or 200)
    gw = (grep_word or "upnp").strip() or "upnp"

    if window_min is None:
        window_min = int(os.environ.get("UPNP_LOG_WINDOW_MIN", "30"))
    window_min = int(window_min)

    now = _dt.datetime.utcnow()
    cutoff = now - _dt.timedelta(minutes=window_min)

    lf_quoted = _shell_quote_single(log_file)

    # NOTE: do NOT use tail -f in automation (will block). Use fixed lines.
    cmd = (
        f"if [ -f {lf_quoted} ]; then "
        f"  tail -n {tail_lines} {lf_quoted} 2>/dev/null | grep -i {_shell_quote_single(gw)} || true; "
        f"else "
        f"  echo '__NO_LOG_FILE__ {log_file}'; "
        f"fi"
    )

    retries = int(os.environ.get("UPNP_SSH_RETRIES", "5"))
    interval = float(os.environ.get("UPNP_SSH_RETRY_INTERVAL_SEC", "2"))
    env_timeout = os.environ.get("UPNP_SSH_TIMEOUT_SEC")
    if env_timeout:
        eff_timeout = float(env_timeout)
    else:
        eff_timeout = 30.0 if float(timeout) == float(DEFAULT_TIMEOUT) else float(timeout)

    last = {"rc": 255, "out": "", "err": "", "sec": 0.0}
    for attempt in range(1, retries + 1):
        rc, out, err, sec = ssh_exec(host, user, password, cmd, timeout=eff_timeout, login_shell=True)
        last = {"rc": rc, "out": out, "err": err, "sec": sec}
        if rc == 0:
            break
        time.sleep(interval)

    text = _strip_ansi(last["out"] or "")
    raw_lines = [l for l in text.splitlines() if l.strip()]

    no_log_file = any(l.startswith("__NO_LOG_FILE__") for l in raw_lines)

    # keep only syslog-like lines containing grep_word
    keep = []
    banner_present = False
    if not no_log_file:
        for l in raw_lines:
            if gw.lower() not in l.lower():
                continue
            if not _SYSLOG_TS_RE.match(l):
                continue
            keep.append(l.rstrip())
        # banner present if we dropped lines
        banner_present = bool(raw_lines and (len(keep) != len(raw_lines)))

    # apply time window using parsed timestamps (best effort)
    recent_lines: list[str] = []
    for line in keep:
        ts = _parse_syslog_time(line, now=now)
        if ts is None:
            recent_lines.append(line)
        else:
            # if timestamp looks wildly off, keep it (avoid false drops)
            if abs((now - ts).total_seconds()) > 60 * 60 * 24 * 90:
                recent_lines.append(line)
            elif ts >= cutoff:
                recent_lines.append(line)

    low = "\n".join(recent_lines).lower()
    bad_keywords = []
    for k in ("error", "failed", "fail", "fatal", "panic"):
        if k in low:
            bad_keywords.append(k)
    bad_keywords = sorted(set(bad_keywords))

    # error_lines legacy: only lines that contain some bad keyword
    error_lines = [l for l in recent_lines if any(k in l.lower() for k in ("error", "fail", "fatal", "panic"))]

    ok = (last["rc"] == 0)
    passed = bool(ok) and (not no_log_file) and (len(bad_keywords) == 0)

    meta = {
        "ok": bool(ok),
        "pass": bool(passed),
        "host": host,
        "user": user,
        "log_file": log_file,
        "rc": last["rc"],
        "sec": last["sec"],
        "timeout": eff_timeout,
        "retries": retries,
        "no_log_file": bool(no_log_file),
        "window_min": int(window_min),
        "tail_lines": int(tail_lines),
        "grep": gw,
        # backward compatible fields
        "line_count": len(recent_lines),
        "lines": recent_lines[-50:],          # 最多最後 50 行 upnp log
        "error_count": len(error_lines),
        "error_lines": error_lines[-20:],     # 最多最後 20 行錯誤
        "stderr": _strip_ansi(last["err"] or "")[-200:],
        # new fields
        "match_count": len(recent_lines),
        "matches": recent_lines[-200:],
        "bad_keywords": bad_keywords,
        "banner_present": banner_present,
        "err": ("no_log_file" if no_log_file else "") or (_strip_ansi(last["err"]) or "").strip()[:400],
        "cmd": cmd,
    }
    return meta

# ---------- DNSv4/v6 via SSH ----------

def _parse_dns_ips(text: str, family: str = "v4") -> list[str]:
    """從 DNS 查詢輸出裡抓出 IP 清單，family 可選 'v4' 或 'v6'。"""
    family = str(family).lower()
    want_v6 = family in ("6", "v6", "ipv6", "aaaa")
    want_v4 = not want_v6

    raw = _strip_ansi(text or "")
    tokens = re.split(r"\s+", raw)
    ips: list[str] = []
    seen: set[str] = set()

    for tok in tokens:
        t = tok.strip(" ,;()[]{}")
        if not t:
            continue
        try:
            ip = ipaddress.ip_address(t)
        except ValueError:
            continue
        if want_v6 and ip.version != 6:
            continue
        if want_v4 and ip.version != 4:
            continue
        s = str(ip)
        if s not in seen:
            seen.add(s)
            ips.append(s)
    return ips

def _parse_nslookup_answer_ips(text: str, domain: str, family: str = "v4") -> list[str]:
    """
    僅從 nslookup 的「Answer 區段」抓出對應 domain 的 IP，
    目標是排除前面 DNS Server 那顆 IP。
    """
    family = str(family).lower()
    want_v6 = family in ("6", "v6", "ipv6", "aaaa")
    want_v4 = not want_v6

    raw = _strip_ansi(text or "")
    lines = raw.splitlines()

    # 正規化 domain（去掉尾巴的 .，轉小寫）
    norm_domain = (domain or "").strip().rstrip(".").lower()

    in_answer = False
    ips: list[str] = []
    seen: set[str] = set()

    for line in lines:
        l = line.strip()
        if not l:
            # 空行就當作區段分隔，跳過
            continue

        low = l.lower()

        # 一般 nslookup 會有：
        #   Name:   www.google.com
        # 從這行之後開始算 answer 區段
        # 或是某些平台會直接在同一行帶 domain
        if ("name:" in low and norm_domain in low) or (
            norm_domain and norm_domain in low and "server:" not in low
        ):
            in_answer = True
            # Name: 這行通常不會有 IP，就不解析，直接看下一行
            continue

        if not in_answer:
            # 還沒進到 answer 區段 → 忽略（通常是 Server/Address 那幾行）
            continue

        # 在 answer 區段裡抓 IP
        # 例如：
        #   Address: 142.250.204.36
        #   Address: 2a00:1450:4009:80d::2004
        for tok in re.findall(r"[0-9a-fA-F:.]+", l):
            try:
                ip = ipaddress.ip_address(tok)
            except ValueError:
                continue
            if want_v6 and ip.version != 6:
                continue
            if want_v4 and ip.version != 4:
                continue
            s = str(ip)
            if s not in seen:
                seen.add(s)
                ips.append(s)

    return ips


def _dns_ip_family(ip: str) -> str | None:
    ip = (ip or "").strip()
    if not ip:
        return None
    ip_norm = ip.strip("[]").split("%", 1)[0]
    try:
        v = ipaddress.ip_address(ip_norm).version
    except Exception:
        return None
    return "v4" if v == 4 else "v6"


def _dns_pick_server_from_resolvconf(
    host: str,
    *,
    user: str,
    password: str,
    family: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> str | None:
    rc, out, err, sec = ssh_exec(
        host,
        user=user,
        password=password,
        cmd="cat /etc/resolv.conf 2>/dev/null || true",
        timeout=timeout,
        login_shell=False,
    )
    if rc != 0 or not out:
        return None

    servers: list[str] = []
    for line in out.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith(";"):
            continue
        if s.lower().startswith("nameserver "):
            parts = s.split()
            if len(parts) >= 2:
                servers.append(parts[1])

    for ns in servers:
        if _dns_ip_family(ns) == family:
            return ns
    return None


def query_dns_records(
    host: str,
    domain: str,
    family: str = "v4",
    *,
    user: str,
    password: str,
    timeout: float = DEFAULT_TIMEOUT,
    dns_server: str | None = None,
    dns_server_family: str = "auto",
) -> tuple[list[str], dict]:
    """Resolve domain on the CPE using nslookup.

    family:
      - v4 => record type A
      - v6 => record type AAAA

    dns_server / dns_server_family control *which resolver* nslookup queries.
      - If dns_server is provided, it is used as the nslookup server argument.
      - Else if dns_server_family is v4/v6, we try to pick a matching nameserver from /etc/resolv.conf.
      - Else (auto): we don't force a server; nslookup uses its default resolver.
    """

    qtype = "A" if family == "v4" else "AAAA"

    dns_server_used: str | None = dns_server
    if not dns_server_used and dns_server_family in ("v4", "v6"):
        dns_server_used = _dns_pick_server_from_resolvconf(
            host, user=user, password=password, family=dns_server_family, timeout=timeout
        )

    base_cmd = f"nslookup -type={qtype} {shlex.quote(domain)}"
    if dns_server_used:
        base_cmd += f" {shlex.quote(dns_server_used)}"
    cmd = f"sh -lc {shlex.quote(base_cmd)}"

    rc, out, err, sec = ssh_exec(
        host, user=user, password=password, cmd=cmd, timeout=timeout, login_shell=True
    )

    raw_ips = _parse_nslookup_answer_ips(out or "", domain=domain, family=family)

    # Filter: keep only IPs of the requested family and drop common resolver-only / captive portal values.
    invalid_ips = {
        "172.14.1.1",
        "127.0.0.53",
        "223.255.255.1",
    }

    valid_ips: list[str] = []
    for ip in raw_ips:
        ip_norm = (ip or "").strip().strip("[]")
        ip_nozone = ip_norm.split("%", 1)[0]

        # Drop the resolver itself if we forced an IP-literal server
        if dns_server_used and _dns_ip_family(dns_server_used) and ip_nozone == dns_server_used.strip("[]").split("%", 1)[0]:
            continue

        fam = _dns_ip_family(ip_nozone)
        if family == "v4" and fam != "v4":
            continue
        if family == "v6" and fam != "v6":
            continue
        if ip_nozone in invalid_ips:
            continue

        valid_ips.append(ip_nozone)

    valid_ips = sorted(set(valid_ips))

    meta = {
        "ok": rc == 0 and len(valid_ips) > 0,
        "rc": rc,
        "sec": sec,
        "raw_count": len(raw_ips),
        "raw_ips": raw_ips,
        "raw_stdout_tail": (out or "")[-800:],
        "raw_stderr_tail": (err or "")[-800:],
    }
    # These are additive fields; existing scripts that only read count/ips won't break.
    meta["dns_server"] = dns_server_used
    meta["dns_server_family"] = dns_server_family

    return valid_ips, meta



def query_dnsv4(host: str,
                domain: str,
                *,
                user: str = None,
                password: str = None,
                timeout: float = DEFAULT_TIMEOUT,
                dns_server: str | None = None,
                dns_server_family: str = "auto"):
    """IPv4(A) 查詢 wrapper。"""
    return query_dns_records(
        host,
        domain,
        family="v4",
        user=user,
        password=password,
        timeout=timeout,
        dns_server=dns_server,
        dns_server_family=dns_server_family,
    )



def query_dnsv6(host: str,
                domain: str,
                *,
                user: str = None,
                password: str = None,
                timeout: float = DEFAULT_TIMEOUT,
                dns_server: str | None = None,
                dns_server_family: str = "auto"):
    """IPv6(AAAA) 查詢 wrapper。"""
    return query_dns_records(
        host,
        domain,
        family="v6",
        user=user,
        password=password,
        timeout=timeout,
        dns_server=dns_server,
        dns_server_family=dns_server_family,
    )


# ---------- iface / MAC address ----------
_MAC_RE = re.compile(r"\b([0-9A-Fa-f]{2}(?:[-:][0-9A-Fa-f]{2}){5})\b")

def _normalize_mac(mac: str) -> str | None:
    if not mac:
        return None
    m = _MAC_RE.search(mac)
    if not m:
        return None
    s = m.group(1).replace("-", ":").upper()
    return s

def get_iface_mac(host: str,
                  iface: str,
                  *,
                  user: str | None = None,
                  password: str | None = None,
                  root_fallback: bool = True,
                  timeout: float = DEFAULT_TIMEOUT):
    """
    透過 SSH 在 CPE 上查詢指定介面的 MAC address。

    回傳 (mac_or_None, meta)

    - 優先讀取 /sys/class/net/<iface>/address（最乾淨、最穩定）
    - fallback：ip link / ifconfig
    - 預設會做 root fallback（與其他 iface helper 一致）
    """
    user = user or _env_any(["SSH_USER", "SSH_USERNAME", "OPERATOR_USER"], "operator")
    password = password or _env_any(["SSH_PASSWORD", "PASSWORD", "CPE_PASSWORD"], "")
    root_user = os.environ.get("SSH_USER_LAN_FALLBACK", "root")
    root_pass = _env_any(["CPE_PASSWORD", "CPE_PASS", "SSH_ROOT_PASSWORD"], password)

    attempts: list[dict] = []

    cmds = [
        f"cat /sys/class/net/{iface}/address 2>/dev/null || true",
        f"ip link show dev {iface} 2>/dev/null || true",
        f"ifconfig {iface} 2>/dev/null || true",
    ]

    def _try(u: str, pw: str):
        for cmd in cmds:
            rc, out, err, sec = ssh_exec(host, u, pw, cmd, timeout=timeout, login_shell=False)
            txt = _strip_ansi((out or "") + "\n" + (err or ""))
            mac = _normalize_mac(txt)
            attempts.append({
                "user": u,
                "cmd": cmd,
                "rc": rc,
                "sec": sec,
                "mac": mac,
                "out": (out or "")[-160:].strip(),
                "err": (err or "")[-160:].strip(),
            })
            if mac:
                return mac, rc, txt
        return None, attempts[-1].get("rc", 255) if attempts else 255, ""

    mac, rc, raw = _try(user, password)

    if (not mac) and root_fallback and (user != root_user) and root_user:
        mac2, rc2, raw2 = _try(root_user, root_pass)
        if mac2:
            mac, rc, raw = mac2, rc2, raw2

    meta = {
        "ok": bool(mac),
        "host": host,
        "iface": iface,
        "mac": mac,
        "rc": rc,
        "attempts": attempts,
        "raw": (raw or "")[-300:],
    }
    return mac, meta


def get_iface_macs(host: str,
                   ifaces: list[str],
                   *,
                   user: str | None = None,
                   password: str | None = None,
                   root_fallback: bool = True,
                   timeout: float = DEFAULT_TIMEOUT):
    """
    批次取得多個介面的 MAC。

    回傳 (macs_dict, meta)
      - macs_dict: { "br-wan": "AA:BB:...", ... }
      - meta     : 每個 iface 的 meta 都會保留在 meta["ifaces"] 方便 debug
    """
    out: dict[str, str | None] = {}
    meta_ifaces: dict[str, dict] = {}

    ok_all = True
    for iface in (ifaces or []):
        m, meta = get_iface_mac(
            host,
            iface,
            user=user,
            password=password,
            root_fallback=root_fallback,
            timeout=timeout,
        )
        out[iface] = m
        meta_ifaces[iface] = meta
        if not m:
            ok_all = False

    meta = {
        "ok": bool(ok_all and out),
        "host": host,
        "count": len(out),
        "macs": out,
        "ifaces": meta_ifaces,
    }
    return out, meta

# ---------- iface / WAN IPv4 ----------
_IPV4_RE = re.compile(r"\binet\s+((?:\d{1,3}\.){3}\d{1,3})/\d+\b")

def _is_bad_ipv4(ip: str, *, allow_link_local: bool = False) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except Exception:
        return True
    if addr.version != 4:
        return True
    if str(addr) == "0.0.0.0":
        return True
    if (not allow_link_local) and addr.is_link_local:
        return True
    return False

def get_iface_ipv4(host: str,
                   iface: str = "br-wan",
                   *,
                   user: str | None = None,
                   password: str | None = None,
                   root_fallback: bool = True,
                   allow_link_local: bool = False,
                   timeout: float = DEFAULT_TIMEOUT):
    """
    透過 SSH 在 CPE 上查詢指定介面的 IPv4。

    回傳 (ipv4_or_None, meta)

    - 預設會排除 0.0.0.0 與 link-local (169.254.0.0/16)
    - 若找不到且 root_fallback=True，會用 root 帳號再試一次
    """
    user = user or _env_any(["SSH_USER", "SSH_USERNAME", "OPERATOR_USER"], "operator")
    password = password or _env_any(["SSH_PASSWORD", "PASSWORD", "CPE_PASSWORD"], "")
    root_user = os.environ.get("SSH_USER_LAN_FALLBACK", "root")
    root_pass = _env_any(["CPE_PASSWORD", "CPE_PASS", "SSH_ROOT_PASSWORD"], password)

    attempts: list[dict] = []

    def _try(u: str, pw: str):
        cmd = f"ip -4 -o addr show dev {iface} 2>/dev/null || true"
        rc, out, err, sec = ssh_exec(host, u, pw, cmd, timeout=timeout, login_shell=True)
        txt = _strip_ansi((out or "") + "\n" + (err or ""))
        ips = []
        for m in _IPV4_RE.finditer(txt):
            ip = m.group(1)
            if not _is_bad_ipv4(ip, allow_link_local=allow_link_local):
                ips.append(ip)
        attempts.append({
            "user": u, "rc": rc, "sec": sec, "cmd": cmd,
            "out": (out or "")[-200:].strip(),
            "err": (err or "")[-200:].strip(),
            "ips": ips,
        })
        return rc, ips, txt

    rc, ips, raw = _try(user, password)
    chosen = ips[0] if ips else None

    if (not chosen) and root_fallback and (user != root_user):
        rc2, ips2, raw2 = _try(root_user, root_pass)
        if ips2:
            chosen = ips2[0]
            raw = raw2
            rc = rc2

    meta = {
        "ok": bool(chosen),
        "host": host,
        "iface": iface,
        "ipv4": chosen,
        "rc": rc,
        "attempts": attempts,
        "raw": (raw or "")[-400:],
    }
    return chosen, meta

def get_br_wan_ipv4(host: str,
                    *,
                    user: str | None = None,
                    password: str | None = None,
                    root_fallback: bool = True,
                    allow_link_local: bool = False,
                    timeout: float = DEFAULT_TIMEOUT):
    """專用 wrapper：查 br-wan 的 IPv4。"""
    return get_iface_ipv4(host, "br-wan",
                          user=user,
                          password=password,
                          root_fallback=root_fallback,
                          allow_link_local=allow_link_local,
                          timeout=timeout)


# ---------- iface / WAN IPv6 ----------
# ip -6 -o addr show dev br-wan  典型輸出：
# 3: br-wan    inet6 2600:....../128 scope global dynamic ...
# 3: br-wan    inet6 fe80::....../64  scope link ...

_IPV6_LINE_RE = re.compile(r"\binet6\s+([0-9a-fA-F:]+)/(\d+)\b.*\bscope\s+(\w+)\b")

def _is_bad_ipv6(ip: str, *, allow_link_local: bool = False) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except Exception:
        return True
    if addr.version != 6:
        return True
    if addr.is_unspecified or addr.is_loopback or addr.is_multicast:
        return True
    if (not allow_link_local) and addr.is_link_local:
        return True
    return False

def get_iface_ipv6(host: str,
                   iface: str = "br-wan",
                   *,
                   user: str | None = None,
                   password: str | None = None,
                   root_fallback: bool = True,
                   allow_link_local: bool = False,
                   require_scope_global: bool = True,
                   timeout: float = DEFAULT_TIMEOUT):
    """
    透過 SSH 在 CPE 上查詢指定介面的 IPv6（預設挑 scope=global）。

    回傳 (ipv6_or_None, meta)

    - 預設排除 unspecified/loopback/multicast，以及 link-local
    - 若 require_scope_global=True，會優先挑 global，找不到才會視 allow_link_local 決定是否退回 link-local
    """
    user = user or _env_any(["SSH_USER", "SSH_USERNAME", "OPERATOR_USER"], "operator")
    password = password or _env_any(["SSH_PASSWORD", "PASSWORD", "CPE_PASSWORD"], "")
    root_user = os.environ.get("SSH_USER_LAN_FALLBACK", "root")
    root_pass = _env_any(["CPE_PASSWORD", "CPE_PASS", "SSH_ROOT_PASSWORD"], password)

    attempts: list[dict] = []

    def _try(u: str, pw: str):
        cmd = f"ip -6 -o addr show dev {iface} 2>/dev/null || true"
        rc, out, err, sec = ssh_exec(host, u, pw, cmd, timeout=timeout, login_shell=True)
        txt = _strip_ansi((out or "") + "\n" + (err or ""))
        addrs = []
        for line in txt.splitlines():
            m = _IPV6_LINE_RE.search(line)
            if not m:
                continue
            ip, plen, scope = m.group(1), int(m.group(2)), m.group(3).lower()
            if _is_bad_ipv6(ip, allow_link_local=allow_link_local):
                continue
            addrs.append({"ip": ip, "prefix_len": plen, "scope": scope})
        attempts.append({
            "user": u, "rc": rc, "sec": sec, "cmd": cmd,
            "out": (out or "")[-200:].strip(),
            "err": (err or "")[-200:].strip(),
            "addrs": addrs,
        })
        return rc, addrs, txt

    rc, addrs, raw = _try(user, password)

    if (not addrs) and root_fallback and (user != root_user):
        rc2, addrs2, raw2 = _try(root_user, root_pass)
        if addrs2:
            addrs, raw, rc = addrs2, raw2, rc2

    chosen = None
    chosen_prefix = None
    if addrs:
        if require_scope_global:
            for a in addrs:
                if a.get("scope") == "global":
                    chosen = a["ip"]
                    chosen_prefix = a.get("prefix_len")
                    break
        if chosen is None:
            chosen = addrs[0]["ip"]
            chosen_prefix = addrs[0].get("prefix_len")

    meta = {
        "ok": bool(chosen),
        "host": host,
        "iface": iface,
        "ipv6": chosen,
        "prefix_len": chosen_prefix,
        "rc": rc,
        "attempts": attempts,
        "raw": (raw or "")[-400:],
    }
    return chosen, meta

def get_iface_lla_ipv6(host: str,
                       iface: str = "br-home",
                       *,
                       user: str | None = None,
                       password: str | None = None,
                       root_fallback: bool = True,
                       timeout: float = DEFAULT_TIMEOUT):
    """
    Get IPv6 link-local (scope=link) address on the given interface.

    Returns:
        (lla_or_None, meta_dict)
    """
    user = user or _env_any(["SSH_USER", "SSH_USERNAME", "OPERATOR_USER"], "operator")
    password = password or _env_any(["SSH_PASSWORD", "PASSWORD", "CPE_PASSWORD"], "")
    root_user = os.environ.get("SSH_USER_LAN_FALLBACK", "root")
    root_pass = _env_any(["CPE_PASSWORD", "CPE_PASS", "SSH_ROOT_PASSWORD"], password)

    attempts: list[dict] = []

    def _try(u: str, pw: str):
        cmd = f"ip -6 -o addr show dev {iface} 2>/dev/null || true"
        rc, out, err, sec = ssh_exec(host, u, pw, cmd, timeout=timeout, login_shell=True)
        txt = _strip_ansi((out or "") + "\n" + (err or ""))

        addrs = []
        for line in txt.splitlines():
            m = _IPV6_LINE_RE.search(line)
            if not m:
                continue
            ip, plen, scope = m.group(1), int(m.group(2)), m.group(3).lower()
            # allow link-local here (we are specifically looking for it)
            if _is_bad_ipv6(ip, allow_link_local=True):
                continue
            addrs.append({"ip": ip, "prefix_len": plen, "scope": scope})

        lla = None
        lla_plen = None
        for a in addrs:
            if a.get("scope") == "link":
                lla = a["ip"]
                lla_plen = a.get("prefix_len")
                break

        attempts.append({
            "user": u,
            "rc": rc,
            "sec": sec,
            "cmd": cmd,
            "lla": lla,
            "addrs": addrs,
            "err": _strip_ansi(err or "")[-160:].strip(),
        })
        return lla, lla_plen, rc, txt, addrs

    lla, plen, rc, raw, addrs = _try(user, password)

    if (not lla) and root_fallback and (user != root_user) and root_user:
        lla2, plen2, rc2, raw2, addrs2 = _try(root_user, root_pass)
        if lla2:
            lla, plen, rc, raw, addrs = lla2, plen2, rc2, raw2, addrs2

    meta = {
        "ok": bool(lla),
        "host": host,
        "iface": iface,
        "lla": lla,
        "prefix_len": plen,
        "rc": rc,
        "attempts": attempts,
        "addrs": addrs,
        "raw": (raw or "")[-400:],
    }
    return lla, meta

def get_br_wan_ipv6(host: str,
                    *,
                    user: str | None = None,
                    password: str | None = None,
                    root_fallback: bool = True,
                    allow_link_local: bool = False,
                    require_scope_global: bool = True,
                    timeout: float = DEFAULT_TIMEOUT):
    """專用 wrapper：查 br-wan 的 IPv6。"""
    return get_iface_ipv6(host, "br-wan",
                          user=user,
                          password=password,
                          root_fallback=root_fallback,
                          allow_link_local=allow_link_local,
                          require_scope_global=require_scope_global,
                          timeout=timeout)


# ---------- ping tools -----------
def ping_from_cpe(host: str,
                  target: str,
                  *,
                  user: str | None = None,
                  password: str | None = None,
                  count: int = 4,
                  timeout: float = DEFAULT_TIMEOUT) -> dict:
    """
    透過 SSH 在 CPE 上對 target 做 ping 測試。

    判定規則：
      - 只要有收到至少 1 個回應，就算 ok=True
      - 「封包有掉」不會直接當 FAIL，而是透過 loss_pct 告訴你
    """
    import re

    user = user or _env_any(["SSH_USER", "SSH_USERNAME", "OPERATOR_USER"], "operator")
    password = password or _env_any(["SSH_PASSWORD", "PASSWORD", "CPE_PASSWORD"], "")

    # 在 CPE 上跑 ping
    c = max(int(count), 1)

    # 根據發包數估一個合理的 timeout（每包抓約 1.5 秒 + 2 秒 buffer）
    est_timeout = 2 + c * 1.5
    eff_timeout = max(timeout, est_timeout)

    cmd = f"ping -c {c} -W 1 {target}"
    # IPv6 target: prefer ping -6 (or ping6 fallback)
    if ":" in str(target):
        cmd = f"ping -6 -c {c} -W 1 {target} || ping6 -c {c} -W 1 {target}"
    rc, out, err, sec = ssh_exec(
        host, user, password,
        cmd,
        timeout=eff_timeout,
        login_shell=True,
    )


    text = _strip_ansi((out or "") + "\n" + (err or ""))

    # 解析 "X packets transmitted, Y received, Z% packet loss"
    sent = recv = 0
    loss_pct = None

    m = re.search(
        r"(\d+)\s+packets transmitted,\s+(\d+)\s+received,[^0-9]*([\d.]+)%\s+packet loss",
        text
    )
    if m:
        sent = int(m.group(1))
        recv = int(m.group(2))
        try:
            loss_pct = float(m.group(3))
        except ValueError:
            loss_pct = None
    else:
        # 解析不到 summary，就用 rc 粗估
        if rc == 0:
            # 一般來說 rc=0 代表至少有回應
            recv = 1
            sent = c
            loss_pct = 0.0
        else:
            sent = c
            recv = 0
            loss_pct = 100.0

    # 允許的最大 loss 百分比（環境變數 SSH_PING_MAX_LOSS，可自行調整）
    max_loss = float(os.environ.get("SSH_PING_MAX_LOSS", "50"))

    if loss_pct is None:
        # 解析不到 summary，就退回原本邏輯：只要有收到一包就當 ok
        ok = (recv > 0)
    else:
        ok = (loss_pct <= max_loss)


    return {
        "ok": ok,
        "rc": rc,
        "sec": sec,
        "host": host,
        "user": user,
        "target": target,
        "sent": sent,
        "received": recv,
        "loss_pct": loss_pct,
        "stdout": text[-400:],   # 最後 400 字元，避免太長
        "stderr": _strip_ansi(err or "")[-200:],
    }
                             

# ---------- health of cpe ---------\
# ---------- CPE HEALTH CHECK (1:1 對應 test2.sh, 加 PATH & banner-safe) ----------
def cpe_health_check(host, user=None, password=None, timeout: float = DEFAULT_TIMEOUT):
    """
    Python 版 CPE Health Check

    - 大致行為對齊 /tmp/test2.sh (OpenSync CPE Health Check v5.7)
    - 特別強化：
      * SSHM：只要 Node_State 裡出現 Clt_Connected 就算 connected
      * SSH ErrorCode：從字串裡「抓最後一個整數」當成 error code，避開 banner 汙染
    """
    import re

    # 預設帳密
    user = user or _env_any(["SSH_USER", "SSH_USERNAME", "OPERATOR_USER"], "operator")
    password = password or _env_any(["SSH_PASSWORD", "PASSWORD", "CPE_PASSWORD"], "")

    results = []
    TOTAL = PASS = FAIL = SKIP = 0

    def OK(msg: str):
        nonlocal TOTAL, PASS
        TOTAL += 1
        PASS += 1
        results.append({"result": "OK", "msg": msg})

    def FAILF(msg: str):
        nonlocal TOTAL, FAIL
        TOTAL += 1
        FAIL += 1
        results.append({"result": "FAIL", "msg": msg})

    def SKIPF(msg: str):
        nonlocal TOTAL, SKIP
        TOTAL += 1
        SKIP += 1
        results.append({"result": "SKIP", "msg": msg})

    def _last_int(text: str):
        """從文字中抓最後一個整數 (避開 SSH Banner/ASCII Art 影響)"""
        txt = _strip_ansi(text or "")
        nums = re.findall(r"\d+", txt)
        return int(nums[-1]) if nums else None

    def _ssh(cmd: str, t: float = None):
        """
        在 CPE 上執行 health 指令：
          - 強制加 PATH 前綴，避免找不到指令
        """
        if t is None:
            t = timeout
        path_prefix = (
            'PATH="/usr/opensync/tools:/usr/opensync/bin:'
            '/usr/sbin:/sbin:/usr/bin:/bin:$PATH"; '
        )
        full_cmd = path_prefix + cmd
        return ssh_exec(host, user, password, full_cmd, timeout=t, login_shell=True)

    def _get_field(dump_text: str, pattern: str) -> str:
        """
        模擬 test2.sh 的 get_field:
          echo "$dump" | grep "$pattern" | awk '{print $NF}' | tr -d '"'
        可能有多行，用 '\\n' 串起來。
        """
        lines = []
        for line in (dump_text or "").splitlines():
            if re.search(pattern, line):
                lines.append(line.split()[-1].strip('"'))
        return "\n".join(lines)

    # ============================================================
    # 1. Checking OVSDB Module Tables
    # ============================================================
    TABLES = [
        ("Wifi_Radio_State", "wm"),
        ("Wifi_VIF_State",   "wm"),
        ("Node_State",       "nm"),
        ("Manager",          "cm"),
    ]

    rc, out, err, _ = _ssh("ovsdb-client list-tables 2>/dev/null")
    tbl_list = [l.strip() for l in (out or "").splitlines() if l.strip()]

    for tbl, mod in TABLES:
        if tbl not in tbl_list:
            SKIPF(f"Module {mod} ({tbl}) not present")
            continue

        cmd = f'timeout 2 ovsdb-client dump "{tbl}" >/dev/null 2>&1'
        rc, _, _, _ = _ssh(cmd)
        if rc == 0:
            OK(f"Module {mod} ({tbl}) responding")
        else:
            FAILF(f"Module {mod} ({tbl}) NOT responding")

    # ============================================================
    # 2. Checking OpenSync Core Processes
    # ============================================================
    PROCS = ["ovsdb-server", "wm", "nm", "cm", "sm", "qm"]

    for p in PROCS:
        rc, pout, _, _ = _ssh(f"pgrep {p} 2>/dev/null | wc -l")
        cnt = _last_int(pout)
        if cnt is None:
            cnt = 0
        if cnt > 0:
            OK(f"{p} running ({cnt} PID)")
        else:
            FAILF(f"{p} NOT running")

    # ============================================================
    # 3. Node_State Modules (NTP / SSHM / Temperature)
    # ============================================================
    rc, NODE_DUMP, _, _ = _ssh("ovsdb-client dump Node_State 2>/dev/null")
    NODE_DUMP = NODE_DUMP or ""
    NODE_DUMP_CLEAN = _strip_ansi(NODE_DUMP)

    # ---------- NTP ----------
    ntp_status = _get_field(NODE_DUMP, r"status.*ntp")
    if "synchronized" in ntp_status:
        OK("NTP synchronized")
    else:
        FAILF("NTP NOT synchronized")

    # ---------- SSH ----------
    # 1) sshStatus：只要 Node_State 裡看到 Clt_Connected 就算 OK
    status_val = _get_field(NODE_DUMP, r"sshStatus")
    if ("Clt_Connected" in NODE_DUMP_CLEAN) or ("Enabled" in status_val):
        OK("SSHM connected")
    else:
        FAILF("SSHM NOT connected")
    # 2) sshErrCode：從字串裡抓「最後一個整數」當成 Error Code
    ssh_err_raw = _get_field(NODE_DUMP, r"sshErrCode").strip()
    err_code = None
    if ssh_err_raw:
        try:
            err_code = int(ssh_err_raw)
        except ValueError:
            err_code = _last_int(ssh_err_raw)

    if err_code is None:
        SKIPF("SSH ErrorCode not reported")
    elif err_code == 0:
        OK("SSH ErrorCode = 0")
    elif err_code == 200:
        # 不當作 FAIL / SKIP，但在訊息裡標示警告
        OK("SSH ErrorCode = 200 (WARNING: platform-specific SSH error code, check with RD)")
    elif err_code == 100:
        SKIPF("SSH ErrorCode = 100 (platform-specific, skipped in health check)")
    else:
        FAILF(f"SSH ErrorCode = {err_code}")

    # ---------- PM Temperature ----------
    temp_str = ""
    for line in NODE_DUMP.splitlines():
        if "Temperature" in line:
            parts = line.split('"')
            if len(parts) >= 3:
                temp_str = parts[1]
                break

    for entry in temp_str.split():
        if ":" not in entry:
            SKIPF(f"Temperature entry parse error: {entry}")
            continue

        sensor, t_str = entry.split(":", 1)
        sensor = sensor.strip()
        t_str = t_str.strip()

        try:
            t = int(t_str)
        except ValueError:
            SKIPF(f"{sensor} temperature parse error ({t_str})")
            continue

        if sensor == "cpu":
            limit = 95
        elif sensor.startswith("wifi"):
            limit = 90
        elif sensor == "iot":
            limit = 85
        else:
            limit = 90

        if t > limit:
            FAILF(f"{sensor} too hot ({t}°C)")
        else:
            OK(f"{sensor} temperature {t}°C")

    # ============================================================
    # 4. Checking Wi-Fi
    # ============================================================
    rc, _, _, _ = _ssh("pgrep hostapd >/dev/null 2>&1")
    if rc == 0:
        OK("hostapd running")
    else:
        FAILF("hostapd NOT running")

    rc, wifi_txt, _, _ = _ssh("iw dev 2>/dev/null")
    wifi_ifaces = []
    for l in (wifi_txt or "").splitlines():
        parts = l.split()
        if len(parts) >= 2 and parts[0] == "Interface":
            wifi_ifaces.append(parts[1])

    for w in wifi_ifaces:
        rc, _, _, _ = _ssh(f"iw dev {w} info >/dev/null 2>&1")
        if rc == 0:
            OK(f"WiFi interface {w} present (iw dev info OK)")
        else:
            FAILF(f"WiFi interface {w} missing or not initialized")

    # ============================================================
    # 5. WAN Connectivity Test
    # ============================================================
    rc, _, _, _ = _ssh("ping -c1 -W1 8.8.8.8 >/dev/null 2>&1")
    if rc == 0:
        OK("WAN ping OK")
    else:
        FAILF("WAN ping FAIL")

    # ---------- Gateway ----------
    rc, gw_raw, _, _ = _ssh("ip route | awk '/^default/ {print $3; exit}'")
    gw_txt = _strip_ansi(gw_raw or "")
    m = re.search(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", gw_txt)
    gw_ip = m.group(0) if m else ""

    if gw_ip:
        rc, _, _, _ = _ssh(f"ping -c1 -W1 {gw_ip} >/dev/null 2>&1")
        if rc == 0:
            OK(f"Gateway {gw_ip} ping OK")
        else:
            FAILF(f"Gateway {gw_ip} ping FAIL")
    else:
        FAILF("No default gateway found")

    # ============================================================
    # 6. DNS Test
    # ============================================================
    rc, _, _, _ = _ssh("nslookup google.com >/dev/null 2>&1")
    if rc == 0:
        OK("DNS resolve OK")
    else:
        FAILF("DNS resolve FAIL")

    # ============================================================
    # 7. Memory Health
    # ============================================================
    rc, mem_avail_raw, _, _ = _ssh("grep MemAvailable /proc/meminfo 2>/dev/null | awk '{print $2}'")
    rc, mem_total_raw, _, _ = _ssh("grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2}'")

    avail_kb = _last_int(mem_avail_raw)
    total_kb = _last_int(mem_total_raw)

    if avail_kb is not None and total_kb is not None and total_kb > 0:
        avail_percent = avail_kb * 100 // total_kb
        if avail_percent < 10:
            FAILF(f"Low available memory: {avail_percent}%")
        else:
            OK(f"Available memory: {avail_percent}%")
    else:
        SKIPF("MemAvailable / MemTotal not found in /proc/meminfo")

    # ============================================================
    # 8. Kernel Crash / Panic Check (pstore)
    #    - 只在偵測到明確的 panic/oops/call trace 關鍵字時才算 FAIL
    #    - 若只有 "REBOOT USER Human Triggered Reboot" 之類的人為重開機訊息 → SKIP
    # ============================================================
    rc, _, _, _ = _ssh("test -d /sys/fs/pstore")
    if rc != 0:
        SKIPF("pstore not present (kernel crash persistence not supported)")
    else:
        # 列出所有看起來像檔名的項目
        rc, pstore_list_raw, _, _ = _ssh("ls -1 /sys/fs/pstore 2>/dev/null || true")
        files = []
        for line in (pstore_list_raw or "").splitlines():
            name = line.strip()
            if not name:
                continue
            # 僅接受真正檔名：console-ramoops-0 / pmsg-ramoops-0 / dmesg-ramoops-0 ...
            if re.fullmatch(r"[A-Za-z0-9._-]+", name):
                files.append(name)

        if not files:
            OK("No kernel crash logs in /sys/fs/pstore")
        else:
            crash_like = False

            for fname in files:
                cat_cmd = (
                    "head -c 4096 "
                    + _shell_quote_single(f"/sys/fs/pstore/{fname}")
                    + " 2>/dev/null"
                )
                rc, content_raw, _, _ = _ssh(cat_cmd)
                content = _strip_ansi(content_raw or "")
                if not content:
                    continue

                low = content.lower()

                # ★ 特例：人為重開機 → 視為非 crash
                # 例如：REBOOT USER Human Triggered Reboot
                if "human triggered reboot" in low or "reboot user human triggered reboot" in low:
                    # 這種 log 直接忽略，不當成 crash
                    continue

                # ★ 真正 crash 關鍵字：只要抓到這幾類就算 FAIL
                if any(k in low for k in ("kernel panic", "panic", "oops", "call trace")):
                    crash_like = True
                    break

            if crash_like:
                FAILF("Kernel crash logs present in /sys/fs/pstore (previous panic/oops)")
            else:
                # 只有人為重開機或非 crash entries → 不拉低 health，記成 SKIP
                SKIPF("pstore contains only user-triggered reboot logs or non-crash entries")


    # ============================================================
    # 9. LAN/WAN Bridge Interface Check
    # ============================================================
    for br in ("br-home", "br-wan"):
        rc, _, _, _ = _ssh(f"ifconfig {br} >/dev/null 2>&1")
        if rc != 0:
            SKIPF(f"Bridge interface {br} not present")
            continue

        rc, ifcfg, _, _ = _ssh(f"ifconfig {br}")
        if "RUNNING" in (ifcfg or ""):
            OK(f"Bridge interface up: {br}")
        else:
            FAILF(f"Bridge interface DOWN: {br}")

    # ============================================================
    # 10. Crash / Dumpcore Check (log_archive)
    #     - /usr/opensync/log_archive/crash       : crashed_sm_* 檔案時間
    #     - /usr/opensync/log_archive/dumpcore.history : 最後一筆 core dump 時間
    #     - 只關心「最近 CRASH_WINDOW 秒」之內的新 crash（預設 1800 秒 = 30 分鐘）
    # ============================================================
    CRASH_WINDOW = int(os.environ.get("CPE_HEALTH_CRASH_WINDOW_SEC", "1800"))

    # 先用 CPE 自己的時間 (避免時區差異問題)
    rc, now_raw, _, _ = _ssh("date +%s")
    now_ts = _last_int(now_raw)
    if now_ts is None:
        SKIPF("Unable to read current time on CPE (date +%s)")
    else:
        # ---------- 10.1 crash/ 目錄 ----------
        rc, crash_list_raw, _, _ = _ssh(
            "ls -1 /usr/opensync/log_archive/crash 2>/dev/null || true"
        )
        crash_files = [
            l.strip()
            for l in (crash_list_raw or "").splitlines()
            if l.strip()
        ]

        if not crash_files:
            OK("No files under /usr/opensync/log_archive/crash")
        else:
            newest_age = None
            newest_name = None

            for fname in crash_files:
                path = f"/usr/opensync/log_archive/crash/{fname}"
                cmd = (
                    f"stat -c %Y {_shell_quote_single(path)} "
                    "2>/dev/null || echo 0"
                )
                rc, epoch_raw, _, _ = _ssh(cmd)
                ts = _last_int(epoch_raw)
                if ts is None:
                    continue

                age = now_ts - ts
                if age < 0:
                    # 時間比現在還「未來」就忽略
                    continue

                if newest_age is None or age < newest_age:
                    newest_age = age
                    newest_name = fname

            if newest_name is None:
                SKIPF("Unable to determine age of crash files in log_archive/crash")
            elif newest_age <= CRASH_WINDOW:
                FAILF(
                    f"Recent crash file {newest_name} in log_archive/crash "
                    f"({newest_age} seconds ago)"
                )
            else:
                OK(
                    f"Last crash file {newest_name} older than "
                    f"{CRASH_WINDOW // 60} minutes ({newest_age} seconds ago)"
                )

        # ---------- 10.2 dumpcore.history ----------
        rc, dump_hist_raw, _, _ = _ssh(
            "cat /usr/opensync/log_archive/dumpcore.history 2>/dev/null || true"
        )
        dump_hist_txt = dump_hist_raw or ""

        def _parse_dumpcore_last_epoch(text: str):
            # 抓最後一個 date:[...]
            matches = re.findall(r"date:\[([^\]]+)\]", text)
            if not matches:
                return None
            last = matches[-1].strip()
            # 範例: Fri May 23 02:58:12 UTC 2025
            dt = None
            try:
                dt = datetime.datetime.strptime(
                    last, "%a %b %d %H:%M:%S %Z %Y"
                )
            except Exception:
                try:
                    # 有些 build 可能沒有 %Z，先拿掉 timezone 再試
                    parts = last.split()
                    if len(parts) >= 6:
                        last2 = " ".join(parts[0:4] + parts[-1:])
                        dt = datetime.datetime.strptime(
                            last2, "%a %b %d %H:%M:%S %Y"
                        )
                except Exception:
                    dt = None

            if dt is None:
                return None
            # 一律用 UTC 來算 epoch
            return calendar.timegm(dt.timetuple())

        if not dump_hist_txt.strip():
            OK("No dumpcore.history entries")
        else:
            last_ts = _parse_dumpcore_last_epoch(dump_hist_txt)
            if last_ts is None:
                SKIPF("Unable to parse dumpcore.history dates")
            else:
                age = now_ts - last_ts
                if 0 <= age <= CRASH_WINDOW:
                    FAILF(
                        "Recent dumpcore entry in "
                        "/usr/opensync/log_archive/dumpcore.history "
                        f"({age} seconds ago)"
                    )
                elif age < 0:
                    SKIPF(
                        "dumpcore.history latest entry is in the future "
                        f"vs CPE clock ({-age} seconds difference)"
                    )
                else:
                    OK(
                        "Last dumpcore.history entry older than "
                        f"{CRASH_WINDOW // 60} minutes ({age} seconds ago)"
                    )

    # ============================================================
    # Summary
    # ============================================================
    overall = "GOOD" if FAIL == 0 else "BAD"

    return {
        "ok": (overall == "GOOD"),
        "overall": overall,
        "total": TOTAL,
        "ok_count": PASS,
        "fail_count": FAIL,
        "skip_count": SKIP,
        "items": results,
    }
    
# ---------- console mute ----------
def _write_mute_file(until_ts: int):
    path = os.environ.get("SERIAL_MUTE_FILE", "/home/da40/charter/var/serial.mute")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(str(int(until_ts)))
    try:
        os.chmod(path, 0o664)
    except Exception:
        pass
    return path

def set_console_mute(seconds: int, *, use_lock: bool = False, lock_timeout: int = 5):
    if not seconds or seconds <= 0:
        return None
    until_ts = int(time.time()) + int(seconds)
    cm = (serial_lock_acquire(block=True, timeout=lock_timeout)
          if (use_lock and serial_lock_acquire) else contextlib.nullcontext())
    with cm:
        if serial_mute and hasattr(serial_mute, "mute_for"):
            try:
                serial_mute.mute_for(int(seconds))
                return until_ts
            except Exception:
                pass
        _write_mute_file(until_ts)
        return until_ts

# ---------- pre logpull ----------
def run_logpull(host, user, password, *, timeout=DEFAULT_PRE_LOGPULL_TIMEOUT):
    cmd = "/usr/opensync/scripts/logpull/logpull.sh --local"
    rc, out, err, sec = ssh_exec(host, user, password, cmd, timeout=timeout, login_shell=True)
    return {"rc": rc, "sec": sec, "out": _strip_ansi(out)[:400], "err": _strip_ansi(err)[:400], "cmd": cmd}

# ---------- remote ops ----------
def list_remote_matches(host, user, password, directory, pattern, *, timeout=DEFAULT_TIMEOUT):
    dirq = _shell_quote_single(directory)
    cmd = f"cd {dirq} && ls -1t 2>/dev/null"
    rc, out, err, sec = ssh_exec(host, user, password, cmd, timeout=timeout, login_shell=True)
    files = _filter_paths(out, directory=directory, pattern=pattern)
    return {"rc": rc, "sec": sec, "files": files, "err": (err or "")[:200].strip()}

def find_latest_remote_file(host, user, password, directory, pattern=DEFAULT_LOGPULL_PATTERN, timeout=DEFAULT_TIMEOUT):
    info = list_remote_matches(host, user, password, directory, pattern, timeout=timeout)
    files = info.get("files") or []
    latest = files[0] if files else None
    return latest, info

def delete_remote_file(host: str, user: str, password: str, path: str,
                       *, timeout: float = DEFAULT_TIMEOUT) -> dict:
    cmd = f"rm -f {_shell_quote_single(path)} 2>/dev/null || true"
    rc, out, err, sec = ssh_exec(host, user, password, cmd, timeout=timeout, login_shell=True)
    return {"ok": (rc == 0), "rc": rc, "sec": sec,
            "out": (out or "")[:200].strip(), "err": (err or "")[:200].strip()}

# ---------- pull-log ----------
def pull_logs(host: str, user: str, password: str,
              sources: list[str], dest: str,
              *, timeout: float = DEFAULT_TIMEOUT, recursive: bool = False,
              delete_remote: bool = False, rename_prefix: str = "") -> dict:
    os.makedirs(dest, exist_ok=True)
    dest_is_dir = os.path.isdir(dest)
    results = []
    for src in sources:
        src = src.strip()
        if not src:
            continue
        remote_paths = []
        if _has_glob(src):
            remote_paths = expand_remote_globs(host, user, password, src, timeout=timeout)
        else:
            remote_paths = [src]
        for rp in remote_paths:
            base = os.path.basename(rp.rstrip("/"))
            local_path = dest if not dest_is_dir else os.path.join(dest, base)
            if rename_prefix:
                final_path = os.path.join(os.path.dirname(local_path), f"{rename_prefix}-{base}")
            else:
                final_path = local_path
            rc, out, err, sec = _scp_download(host, user, password, rp, final_path, timeout=timeout, recursive=recursive)
            #del_meta = None
            #if rc == 0 and delete_remote:
            #    ok_del, del_meta = delete_remote_file(host, user, password, rp, timeout=timeout)
            del_meta = None
            if rc == 0 and delete_remote:
                del_meta = delete_remote_file(host, user, password, rp, timeout=timeout)
            results.append({
                "src": rp,
                "dest": final_path if (rc == 0) else (local_path if dest_is_dir else dest),
                "rc": rc, "sec": sec,
                "out": (out or "")[:200].strip(), "err": (err or "")[:200].strip(),
                "deleted": bool(del_meta and del_meta.get("ok")), "delete_meta": del_meta,
            })
    ok = all(r["rc"] == 0 for r in results) if results else False
    return {"ok": ok, "results": results}

def expand_remote_globs(host: str, user: str, password: str, pattern: str,
                        *, timeout: float = DEFAULT_TIMEOUT) -> list[str]:
    directory = os.path.dirname(pattern) or "."
    basepat = os.path.basename(pattern) or "*"
    cmd = f"cd {_shell_quote_single(directory)} && ls -1 2>/dev/null"
    rc, out, err, sec = ssh_exec(host, user, password, cmd, timeout=timeout, login_shell=True)
    if rc != 0:
        return [pattern]
    return _filter_paths(out, directory=directory, pattern=basepat)

def pull_latest_log(host: str, user: str, password: str,
                    directory: str, pattern: str,
                    dest_dir: str, *, timeout: float = DEFAULT_TIMEOUT,
                    delete_remote: bool = False, rename_prefix: str = "") -> tuple[bool, dict]:
    latest, info = find_latest_remote_file(host, user, password, directory, pattern=pattern, timeout=timeout)
    if not latest:
        return False, {"step": "list", "list": info}
    os.makedirs(dest_dir, exist_ok=True)
    base = os.path.basename(latest)
    local_path = os.path.join(dest_dir, base)
    if rename_prefix:
        local_path = os.path.join(dest_dir, f"{rename_prefix}-{base}")
    rc, out, err, sec = _scp_download(host, user, password, latest, local_path, timeout=timeout)
    meta = {"step": "pull-latest", "latest": latest, "dest": local_path,
            "rc": rc, "sec": sec, "err": (err or "")[:200].strip(), "list": info}
    if rc == 0 and delete_remote:
        del_meta = delete_remote_file(host, user, password, latest, timeout=timeout)
        meta["delete"] = del_meta
    return rc == 0, meta


# ---------- metrics ----------
def _parse_first_number(s: str):
    if not s:
        return None
    m = re.search(r"(-?\d+(?:\.\d+)?)", s)
    if not m:
        return None
    try:
        return float(m.group(1))
    except Exception:
        return None


def collect_basic_metrics(
    host,
    *,
    iface="br-wan",
    user=None,
    password=None,
    timeout=DEFAULT_TIMEOUT,
    rate_interval=1.0,
    latency_target=None,
    latency_ms=None,
    root_fallback=True,
):
    """Collect best-effort basic metrics via SSH.

    Returns dict:
      { ok, cpu_pct, mem_pct, temp_c, rx_mbps, tx_mbps, latency_ms, iface, host, rc, errors, attempts }
    """
    errors = []
    attempts = []

    users = [user] if user else []
    if root_fallback and "root" not in users:
        users.append("root")

    for u in users:
        pw = password

        # CPU (sample twice on-box)
        cpu_pct = None
        cmd_cpu = (
            "awk '/^cpu /{print $2,$3,$4,$5,$6,$7,$8,$9,$10}' /proc/stat; "
            "sleep 0.25; "
            "awk '/^cpu /{print $2,$3,$4,$5,$6,$7,$8,$9,$10}' /proc/stat"
        )
        rc1, out1, err1, sec1 = ssh_exec(host, u, pw, cmd_cpu, timeout=timeout, login_shell=False)
        if rc1 == 0 and out1:
            lines = [ln.strip() for ln in out1.splitlines() if ln.strip()]
            num_lines = [ln for ln in lines if re.fullmatch(r"[0-9.\s]+", ln)]
            if len(num_lines) >= 2:
                try:
                    a = [float(x) for x in num_lines[-2].split()]
                    b = [float(x) for x in num_lines[-1].split()]
                    ta, tb = sum(a), sum(b)
                    idle_a = a[3] + (a[4] if len(a) > 4 else 0.0)
                    idle_b = b[3] + (b[4] if len(b) > 4 else 0.0)
                    dt = max(1e-9, tb - ta)
                    didle = idle_b - idle_a
                    cpu_pct = max(0.0, min(100.0, (1.0 - didle / dt) * 100.0))
                except Exception as e:
                    errors.append(f"cpu_parse:{type(e).__name__}")
        elif err1:
            errors.append(f"cpu_cmd:{err1.strip()[:120]}")

        # Mem (MemTotal/MemAvailable)
        mem_pct = None
        cmd_mem = "awk '/MemTotal:/{t=$2}/MemAvailable:/{a=$2} END{print t,a}' /proc/meminfo"
        rc2, out2, err2, sec2 = ssh_exec(host, u, pw, cmd_mem, timeout=timeout, login_shell=False)
        if rc2 == 0 and out2:
            nums = re.findall(r"\b\d+(?:\.\d+)?\b", out2)
            if len(nums) >= 2:
                try:
                    total = float(nums[0])
                    avail = float(nums[1])
                    if total > 0:
                        mem_pct = max(0.0, min(100.0, (1.0 - (avail / total)) * 100.0))
                except Exception as e:
                    errors.append(f"mem_parse:{type(e).__name__}")
        elif err2:
            errors.append(f"mem_cmd:{err2.strip()[:120]}")

        # Temp (first available thermal zone)
        temp_c = None
        cmd_temp = 'for p in /sys/class/thermal/thermal_zone*/temp /sys/devices/virtual/thermal/thermal_zone*/temp; do [ -r "$p" ] && cat "$p" && break; done'
        rc3, out3, err3, sec3 = ssh_exec(host, u, pw, cmd_temp, timeout=timeout, login_shell=False)
        if rc3 == 0 and out3:
            val = _parse_first_number(out3)
            if val is not None:
                temp_c = (val / 1000.0) if val > 200 else val

        # RX/TX Mbps (sample counters)
        rx_mbps = None
        tx_mbps = None
        try:
            interval = float(rate_interval)
            if interval <= 0:
                interval = 1.0
        except Exception:
            interval = 1.0

        cmd_rate = (
            f"rx1=$(cat /sys/class/net/{iface}/statistics/rx_bytes 2>/dev/null || echo 0); "
            f"tx1=$(cat /sys/class/net/{iface}/statistics/tx_bytes 2>/dev/null || echo 0); "
            f"sleep {interval}; "
            f"rx2=$(cat /sys/class/net/{iface}/statistics/rx_bytes 2>/dev/null || echo 0); "
            f"tx2=$(cat /sys/class/net/{iface}/statistics/tx_bytes 2>/dev/null || echo 0); "
            f"echo $rx1 $rx2 $tx1 $tx2"
        )
        rc4, out4, err4, sec4 = ssh_exec(host, u, pw, cmd_rate, timeout=timeout + interval + 2, login_shell=False)
        if rc4 == 0 and out4:
            nums = re.findall(r"\b\d+\b", out4)
            if len(nums) >= 4:
                try:
                    rx1, rx2, tx1, tx2 = [int(x) for x in nums[:4]]
                    rx_mbps = max(0.0, ((rx2 - rx1) * 8.0) / (interval * 1e6))
                    tx_mbps = max(0.0, ((tx2 - tx1) * 8.0) / (interval * 1e6))
                except Exception as e:
                    errors.append(f"rate_parse:{type(e).__name__}")

        # Latency (optional)
        lat = None
        if latency_ms is not None:
            try:
                lat = float(latency_ms)
            except Exception:
                lat = None
        elif latency_target:
            cmd_lat = (
                "ping -c 1 -W 1 " + str(latency_target)
                + " 2>/dev/null | awk -F'time=' '/time=/{print $2}' | awk '{print $1}' | head -1"
            )
            rc5, out5, err5, sec5 = ssh_exec(host, u, pw, cmd_lat, timeout=timeout, login_shell=False)
            if rc5 == 0 and out5:
                lat = _parse_first_number(out5)

        ok = (cpu_pct is not None and mem_pct is not None)
        result = {
            "ok": bool(ok),
            "host": host,
            "iface": iface,
            "cpu_pct": cpu_pct,
            "mem_pct": mem_pct,
            "temp_c": temp_c,
            "rx_mbps": rx_mbps,
            "tx_mbps": tx_mbps,
            "latency_ms": lat,
            "user": u,
            "errors": list(errors),
        }
        attempts.append(result)
        if ok:
            return {**result, "attempts": attempts, "rc": 0}

    last = attempts[-1] if attempts else {"ok": False, "host": host, "iface": iface, "errors": errors}
    return {**last, "attempts": attempts, "rc": 1}



# ---------- Wi-Fi credentials (default/current) ----------
_MF_TOOL_KV_RE = re.compile(r'^\s*([A-Za-z0-9_]+)\s*:\s*\[([^\]]*)\]\s*$')

def _parse_mf_tool_show(text: str) -> dict:
    """Parse `mf_tool show` key/value output into a dict."""
    raw = _strip_ansi(text or "")
    out: dict = {}
    for line in raw.splitlines():
        m = _MF_TOOL_KV_RE.match(line)
        if not m:
            continue
        k = m.group(1).strip()
        v = m.group(2).strip()
        out[k] = v
    return out

def _parse_ovsh_table(text: str) -> list[dict]:
    """
    Parse `ovsh s <Table> -c col...` output (multi-row table) into list of dict rows.
    Best-effort; ignores banners/ANSI and separator lines.
    """
    raw = _strip_ansi(text or "")
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    # remove obvious separator lines
    def _is_sep(l: str) -> bool:
        if l.startswith("---"):
            return True
        s = set(l)
        return s.issubset(set("-+| "))
    lines = [l for l in lines if not _is_sep(l)]

    header = None
    header_i = None
    for i, l in enumerate(lines):
        if "|" not in l:
            continue
        parts = [p.strip() for p in l.split("|")]
        # trim leading/trailing empties from pipes
        if parts and parts[0] == "":
            parts = parts[1:]
        if parts and parts[-1] == "":
            parts = parts[:-1]
        parts = [p for p in parts if p != ""]
        if not parts:
            continue
        # header typically contains known column names
        if any(p in ("if_name", "ssid", "wpa_psks") for p in parts):
            header = parts
            header_i = i
            break

    if not header:
        return []

    rows: list[dict] = []
    for l in lines[(header_i + 1):]:
        if "|" not in l:
            continue
        parts = [p.strip() for p in l.split("|")]
        if parts and parts[0] == "":
            parts = parts[1:]
        if parts and parts[-1] == "":
            parts = parts[:-1]
        # keep empties in the middle; just ensure length
        if len(parts) < len(header):
            continue
        row = {}
        for k, v in zip(header, parts[:len(header)]):
            row[k] = v.strip()
        rows.append(row)
    return rows

def _extract_psk_from_wpa_psks(val: str) -> str | None:
    """Extract PSK from ovsh wpa_psks field.

    Tolerates formats like:
      ["map",[["key-1","pass..."]]]
      ["map",[["key--1","pass..."]]]
    """
    if not val:
        return None
    s = str(val).strip()
    if s in ("[]", "null", "None"):
        return None
    try:
        obj = __import__('json').loads(s)
        if isinstance(obj, list) and len(obj) >= 2 and obj[0] == "map":
            pairs = obj[1]
            if isinstance(pairs, list):
                # Prefer a key that normalizes to "key1" (key-1 / key--1 / key_1 etc)
                for pair in pairs:
                    if not isinstance(pair, list) or len(pair) < 2:
                        continue
                    k, v = pair[0], pair[1]
                    k_norm = re.sub(r"[^A-Za-z0-9]", "", str(k)).lower()
                    if k_norm == "key1":
                        return str(v)
                # else fallback: first pair value
                if pairs and isinstance(pairs[0], list) and len(pairs[0]) >= 2:
                    return str(pairs[0][1])
        if isinstance(obj, str):
            return obj
    except Exception:
        pass
    # fallback: last quoted string
    m = re.findall(r'"([^"]+)"', s)
    return m[-1] if m else None


def _run_with_optional_root(host: str, user: str, password: str,
                            root_fallback: bool, timeout: float, cmd: str,
                            *, login_shell: bool = True):
    """Run cmd as user, optionally fallback to root. Return (used_user, rc, out, err, sec)."""
    rc, out, err, sec = ssh_exec(host, user, password, cmd, timeout=timeout, login_shell=login_shell)
    if rc == 0:
        return user, rc, out, err, sec

    if root_fallback:
        root_user = os.environ.get("SSH_USER_LAN_FALLBACK", "root")
        root_pass = _env_any(["CPE_PASSWORD", "CPE_PASS", "SSH_ROOT_PASSWORD"], password)
        if root_user and root_user != user:
            rc2, out2, err2, sec2 = ssh_exec(host, root_user, root_pass, cmd, timeout=timeout, login_shell=login_shell)
            # Only override when root actually succeeds
            if rc2 == 0:
                return root_user, rc2, out2, err2, sec2

    return user, rc, out, err, sec



# ---------- DHCP (reserved/leased) via ovsh ----------

def _parse_ovsh_keyed_columns(text: str, allowed_keys: set[str] | None = None) -> list[dict]:
    """Parse `ovsh s <TABLE>` output into list[dict].

    - Vertical style (multiple records):
        ------------------------------
        key | value |
        ...
        ------------------------------
      => returns N dicts (one per record)

    - Horizontal style (one table with many columns):
        key | v1 | v2 | ...
        key : v1 | v2 | ...   (key + first value in same segment)
      => returns N dicts (one per column/record)

    allowed_keys: if provided, only keep these keys (prevents parsing login banners with pipes).
    """
    raw = _strip_ansi(text or "")
    lines = raw.splitlines()

    def _is_sep_line(l: str) -> bool:
        s = (l or "").strip()
        if not s:
            return False
        if s.startswith("---"):
            return True
        return set(s).issubset(set("-+| "))

    def _extract_parts(line: str):
        if "|" not in line:
            return None
        raw_parts = line.split("|")
        # drop trailing empty cell caused by ending "|" (common in ovsh)
        if raw_parts and raw_parts[-1].strip() == "":
            raw_parts = raw_parts[:-1]
        # keep empty columns (important for horizontal keyed-columns output)
        parts = [p.strip() for p in raw_parts]
        if len(parts) < 2:
            return None
        first = parts[0]
        rest = parts[1:]

        if ":" in first:
            k, v1 = first.split(":", 1)
            key = k.strip()
            vals = [v1.strip()] + [x.strip() for x in rest]
        else:
            key = first.strip()
            vals = [x.strip() for x in rest]
        if allowed_keys is not None and key not in allowed_keys:
            return None
        return key, vals

    # Decide format: horizontal if any valid line has >1 value column
    candidate = []
    for l in lines:
        if _is_sep_line(l):
            continue
        r = _extract_parts(l)
        if not r:
            continue
        key, vals = r
        candidate.append((key, vals))
    horizontal = any(len(vals) > 1 for _, vals in candidate)

    if horizontal:
        records: list[dict] = []
        for l in lines:
            if _is_sep_line(l):
                continue
            r = _extract_parts(l)
            if not r:
                continue
            key, vals = r
            if not records:
                records = [{} for _ in range(len(vals))]
            elif len(records) < len(vals):
                records.extend({} for _ in range(len(vals) - len(records)))
            for i, v in enumerate(vals):
                records[i][key] = v
        return [r for r in records if r]
    else:
        # Vertical blocks split by separator lines
        records: list[dict] = []
        cur: dict = {}
        for l in lines:
            if _is_sep_line(l):
                if cur:
                    records.append(cur)
                    cur = {}
                continue
            r = _extract_parts(l)
            if not r:
                continue
            key, vals = r
            cur[key] = vals[0] if vals else ""
        if cur:
            records.append(cur)
        return [r for r in records if r]


def _normalize_keyed_rows_to_records(
    rows: list[dict],
    *,
    key_field: str = "if_name",
    allowed_keys: set[str] | None = None,
) -> list[dict]:
    """Normalize ovsh parsed rows into record-wise dicts.

    Some parsers produce a *row-wise keyed table* like:
        [{"if_name":"mac","home-ap-50":"..","home-ap-24":".."}, ...]
    This helper pivots it into record-wise:
        [{"if_name":"home-ap-50","mac":"..", ...}, ...]
    """
    if not rows:
        return []

    # Heuristic: row-wise keyed table has key_field plus >=2 other columns,
    # and many key_field values look like field names (mac/ssid/enabled/_uuid...)
    if isinstance(rows, list) and isinstance(rows[0], dict) and key_field in rows[0]:
        other_cols = [k for k in rows[0].keys() if k != key_field]
        if other_cols:
            known_fields = {
                "_uuid", "_version", "if_name", "mac", "enabled", "ssid", "ssid_broadcast",
                "freq_band", "channel", "ht_mode", "hw_mode", "tx_power", "country",
                "vif_states", "wpa_key_mgmt",
            }
            sample = rows[:20]
            field_like = 0
            for r in sample:
                v = str(r.get(key_field, "")).strip()
                if v in known_fields or v.startswith("_") or re.match(r"^[a-z][a-z0-9_]*$", v):
                    field_like += 1
            col_like = 0
            for c in other_cols[:10]:
                if re.match(r"^(wifi\d+|home-ap-\d+|.*-ap-\d+)$", str(c)):
                    col_like += 1
            rowwise = (field_like >= max(3, len(sample) // 3)) and (len(other_cols) >= 2 or col_like >= 2)

            if rowwise:
                # Optional filter by allowed_keys (field names)
                filtered = rows
                if allowed_keys is not None:
                    filtered = []
                    for r in rows:
                        fname = str(r.get(key_field, "")).strip()
                        if fname in allowed_keys:
                            filtered.append(r)

                cols = other_cols
                rec_map: dict[str, dict] = {c: {key_field: c} for c in cols}
                for r in filtered:
                    fname = str(r.get(key_field, "")).strip()
                    if not fname:
                        continue
                    for c in cols:
                        if c in r:
                            rec_map[c][fname] = r[c]
                return [rec_map[c] for c in cols if rec_map[c]]

    # Record-wise; optionally trim keys
    if allowed_keys is not None:
        out: list[dict] = []
        for r in rows:
            if not isinstance(r, dict):
                continue
            nr = {}
            for k, v in r.items():
                if k == key_field or k in allowed_keys:
                    nr[k] = v
            out.append(nr)
        return out

    return rows
def _ovsh_dump_table(host: str, table: str, *,
                    user: str | None = None,
                    password: str | None = None,
                    root_fallback: bool = True,
                    timeout: float = DEFAULT_TIMEOUT) -> tuple[list[dict] | None, dict]:
    """
    Run: ovsh s <table>
    Return: (rows_or_none, meta)
    """
    user = user or _env_any(["SSH_USER", "SSH_USERNAME", "OPERATOR_USER"], "operator")
    password = password or _env_any(["SSH_PASSWORD", "PASSWORD", "CPE_PASSWORD"], "")

    # Only accept known ovsh keys to avoid parsing login banners (which may contain '|')
    allowed = None
    if table == "DHCP_reserved_IP":
        allowed = {"_uuid", "_version", "hostname", "hw_addr", "ip_addr"}
    elif table == "DHCP_leased_IP":
        allowed = {"_uuid", "_version", "fingerprint", "hostname", "hwaddr", "inet_addr", "lease_time", "vendor_class"}

    cmd = OVSH_CHAIN.format(args=f"s {table} 2>/dev/null")
    used_user, rc, out, err, sec = _run_with_optional_root(
        host, user, password, root_fallback, timeout, cmd,
        login_shell=False,  # prevent profile/banner pollution
    )

    text_all = (out or "") + "\n" + (err or "")
    rows = _parse_ovsh_keyed_columns(text_all, allowed_keys=allowed)

    # add convenient normalized fields (non-breaking: only adds extra keys)
    for r in rows:
        if r.get("hw_addr"):
            r["mac"] = _normalize_mac(r.get("hw_addr")) or r.get("hw_addr")
        if r.get("hwaddr"):
            r["mac"] = _normalize_mac(r.get("hwaddr")) or r.get("hwaddr")
        if r.get("ip_addr"):
            r["ip"] = r.get("ip_addr")
        if r.get("inet_addr"):
            r["ip"] = r.get("inet_addr")

    meta = {
        "ok": bool(rows),
        "host": host,
        "table": table,
        "user": used_user,
        "rc": rc,
        "sec": sec,
        "cmd": cmd,
        "stderr": _strip_ansi(err or "")[-200:],
        "raw_tail": _strip_ansi(text_all)[-800:],
    }
    return (rows if rows else None), meta
def get_dhcp_reserved_ips(host: str, *,
                          user: str | None = None,
                          password: str | None = None,
                          root_fallback: bool = True,
                          timeout: float = DEFAULT_TIMEOUT) -> tuple[list[dict] | None, dict]:
    """ovsh s DHCP_reserved_IP"""
    return _ovsh_dump_table(
        host, "DHCP_reserved_IP",
        user=user, password=password,
        root_fallback=root_fallback,
        timeout=timeout,
    )


def get_dhcp_leased_ips(host: str, *,
                        user: str | None = None,
                        password: str | None = None,
                        root_fallback: bool = True,
                        timeout: float = DEFAULT_TIMEOUT) -> tuple[list[dict] | None, dict]:
    """ovsh s DHCP_leased_IP"""
    return _ovsh_dump_table(
        host, "DHCP_leased_IP",
        user=user, password=password,
        root_fallback=root_fallback,
        timeout=timeout,
    )


def get_dhcp_info(host: str, *,
                  user: str | None = None,
                  password: str | None = None,
                  root_fallback: bool = True,
                  timeout: float = DEFAULT_TIMEOUT) -> dict:
    """Convenience: fetch both reserved + leased."""
    reserved, meta_r = get_dhcp_reserved_ips(
        host, user=user, password=password, root_fallback=root_fallback, timeout=timeout
    )
    leased, meta_l = get_dhcp_leased_ips(
        host, user=user, password=password, root_fallback=root_fallback, timeout=timeout
    )
    ok = bool(reserved) or bool(leased)
    return {
        "ok": ok,
        "host": host,
        "reserved_count": len(reserved or []),
        "leased_count": len(leased or []),
        "reserved": reserved or [],
        "leased": leased or [],
        "meta": {"reserved": meta_r, "leased": meta_l},
    }


def get_wifi_creds_default(host: str, *, user: str, password: str, root_fallback: bool, timeout: float) -> tuple[dict | None, dict]:
    """
    Return default (manufacturing/label) SSID/PSK from `mf_tool show`.
    """
    cmd = "mf_tool show 2>/dev/null"
    used_user, rc, out, err, sec = _run_with_optional_root(host, user, password, root_fallback, timeout, cmd)
    kv = _parse_mf_tool_show((out or "") + "\n" + (err or ""))
    def _band(ssid_key, psk_key):
        ssid = kv.get(ssid_key)
        psk = kv.get(psk_key)
        if ssid is None and psk is None:
            return None
        return {"ssid": ssid, "psk": psk}
    data = {
        "2g": _band("WLAN2GSSID", "WLAN2GPassword"),
        "5g": _band("WLAN5GSSID", "WLAN5GPassword"),
        "6g": _band("WLAN6GSSID", "WLAN6GPassword"),
    }
    # drop None bands
    data = {k: v for k, v in data.items() if v is not None}
    ok = bool(data)
    meta = {"ok": ok, "source": "mf_tool", "user": used_user, "rc": rc, "sec": sec, "stderr": _strip_ansi(err or "")[-200:]}
    return (data if ok else None), meta

def get_wifi_creds_current(host: str, *, user: str, password: str, root_fallback: bool, timeout: float) -> tuple[dict | None, dict]:
    """Return current (runtime) SSID/PSK from `ovsh Wifi_VIF_Config`.

    Notes:
      - Some platforms output pipe-table format; others output key: value blocks.
      - We use a robust parser that handles both.
    """
    # IMPORTANT: do NOT use -r here; many builds print block-style output without it.
    cmd = OVSH_CHAIN.format(args="s Wifi_VIF_Config -c if_name -c ssid -c wpa_psks 2>/dev/null")
    used_user, rc, out, err, sec = _run_with_optional_root(host, user, password, root_fallback, timeout, cmd)

    raw = (out or "") + "\n" + (err or "")
    # First try table parser, then fallback to block/kv parser.
    rows = _parse_ovsh_table(raw)
    if not rows:
        rows = _parse_ovsh_wifi_vif_config(raw)

    vifs = []
    for r in rows:
        if_name = (r.get("if_name") or "").strip() or None
        ssid = (r.get("ssid") or "").strip() or None
        raw_psks = (r.get("wpa_psks") or "").strip() or None
        psk = _extract_psk_from_wpa_psks(raw_psks or "")
        if not (if_name or ssid or psk):
            continue
        vifs.append({"if_name": if_name, "ssid": ssid, "psk": psk})

    ok = bool(vifs)
    meta = {"ok": ok, "source": "ovsh", "user": used_user, "rc": rc, "sec": sec, "stderr": _strip_ansi(err or "")[-200:]}
    return ({"vifs": vifs} if ok else None), meta

def get_wifi_creds(host: str, *, user: str = None, password: str = None,
                   root_fallback: bool = True, timeout: float = DEFAULT_TIMEOUT,
                   which: str = "both") -> dict:
    """
    which: current | default | both
    Output includes PSK (password).
    """
    user = user or _env_any(["SSH_USER", "SSH_USERNAME", "OPERATOR_USER"], "operator")
    password = password or _env_any(["SSH_PASSWORD", "PASSWORD", "CPE_PASSWORD"], "")

    which = (which or "both").lower()
    if which not in ("current", "default", "both"):
        which = "both"

    out = {"ok": False, "host": host, "which": which}

    metas = {}
    if which in ("default", "both"):
        data, meta = get_wifi_creds_default(host, user=user, password=password, root_fallback=root_fallback, timeout=timeout)
        out["default"] = data
        metas["default"] = meta

    if which in ("current", "both"):
        data, meta = get_wifi_creds_current(host, user=user, password=password, root_fallback=root_fallback, timeout=timeout)
        out["current"] = data
        metas["current"] = meta

    out["meta"] = metas
    # ok if the requested section(s) succeeded
    if which == "default":
        out["ok"] = bool(out.get("default"))
    elif which == "current":
        out["ok"] = bool(out.get("current"))
    else:
        out["ok"] = bool(out.get("default") or out.get("current"))
    return out



# ---------- Wi-Fi state tables (Wifi_VIF_State / Wifi_Radio_State) ----------

def get_wifi_vif_state(host: str, *,
                       user: str | None = None,
                       password: str | None = None,
                       root_fallback: bool = True,
                       timeout: float = DEFAULT_TIMEOUT) -> dict:
    """
    Return Wifi_VIF_State rows.

    Notes:
      - On some FW, `ovsh s Wifi_VIF_State` prints "keyed-columns" (field names on left, records as columns).
        We parse that into list[dict] (one dict per VIF).
      - We intentionally select a practical subset of columns to avoid multiline wrap on huge fields (e.g. wpa_psks).
    """
    table = "Wifi_VIF_State"
    user = user or _env_any(["SSH_USER", "SSH_USERNAME", "OPERATOR_USER"], "operator")
    password = password or _env_any(["SSH_PASSWORD", "PASSWORD", "CPE_PASSWORD"], "")

    # Parse only a practical subset (avoid huge/multiline fields like wpa_psks that can wrap)
    allowed = {
        "_uuid", "_version",
        "if_name", "ssid", "enabled", "ssid_broadcast",
        "channel", "vif_radio_idx",
        "mac", "mode", "min_hw_mode",
        "pmf", "wpa", "wpa_key_mgmt",
    }

    # IMPORTANT: do NOT use `-c` here. On some FW, `ovsh s <TABLE> -c ...` changes format and breaks parsing.
    # Plain `ovsh s <TABLE>` consistently shows keyed-columns output (records are columns).
    cmd = OVSH_CHAIN.format(args=f"s {table} 2>/dev/null")

    used_user, rc, out, err, sec = _run_with_optional_root(
        host, user=user, password=password, cmd=cmd, root_fallback=root_fallback, timeout=timeout, login_shell=False
    )

    res = {
        "ok": False,
        "host": host,
        "table": table,
        "count": 0,
        "rows": [],
        "user": used_user,
        "rc": rc,
        "sec": sec,
    }
    if rc != 0:
        res["stderr"] = (err or "").strip()
        res["stdout"] = (out or "").strip()
        return res

    raw = out or ""
    # Prefer keyed-columns parser for ovsh "s" output; fallback to row-table parsing.
    rows = _parse_ovsh_keyed_columns(raw, allowed_keys=allowed)
    if not rows:
        rows = _parse_ovsh_table(raw)
    rows = _normalize_keyed_rows_to_records(rows, key_field="if_name", allowed_keys=allowed)

    # Post-process booleans commonly used by test plans
    norm_rows: list[dict] = []
    for r in (rows or []):
        rr = dict(r)
        if "enabled" in rr:
            rr["enabled_bool"] = str(rr.get("enabled", "")).strip().lower() in ("true", "1", "yes", "enabled", "on")
        if "ssid_broadcast" in rr:
            rr["ssid_broadcast_bool"] = str(rr.get("ssid_broadcast", "")).strip().lower() in ("enabled", "true", "1", "yes", "on")
        norm_rows.append(rr)

    res["rows"] = norm_rows
    res["count"] = len(norm_rows)
    res["ok"] = True
    return res


def get_wifi_radio_state(host: str, *,
                         user: str | None = None,
                         password: str | None = None,
                         root_fallback: bool = True,
                         timeout: float = DEFAULT_TIMEOUT) -> dict:
    """
    Return Wifi_Radio_State rows (typically 2.4G/5G/6G).
    """
    table = "Wifi_Radio_State"
    user = user or _env_any(["SSH_USER", "SSH_USERNAME", "OPERATOR_USER"], "operator")
    password = password or _env_any(["SSH_PASSWORD", "PASSWORD", "CPE_PASSWORD"], "")

    # Keep only a practical subset (avoid huge/multiline fields like channels maps that can wrap)
    allowed = {
        "_uuid", "_version",
        "if_name", "enabled", "freq_band",
        "channel", "ht_mode", "hw_mode", "hw_type",
        "tx_power", "tx_chainmask",
    }

    # IMPORTANT: do NOT use `-c` here. On some FW, `ovsh s <TABLE> -c ...` changes format and breaks parsing.
    cmd = OVSH_CHAIN.format(args=f"s {table} 2>/dev/null")

    used_user, rc, out, err, sec = _run_with_optional_root(
        host, user=user, password=password, cmd=cmd, root_fallback=root_fallback, timeout=timeout, login_shell=False
    )

    res = {
        "ok": False,
        "host": host,
        "table": table,
        "count": 0,
        "rows": [],
        "user": used_user,
        "rc": rc,
        "sec": sec,
    }
    if rc != 0:
        res["stderr"] = (err or "").strip()
        res["stdout"] = (out or "").strip()
        return res

    raw = out or ""


    # Prefer keyed-columns parser for ovsh \"s\" output; fallback to row-table parsing.


    rows = _parse_ovsh_keyed_columns(raw, allowed_keys=allowed)


    if not rows:


        rows = _parse_ovsh_table(raw)


    rows = _normalize_keyed_rows_to_records(rows, key_field="if_name", allowed_keys=allowed)

    norm_rows: list[dict] = []
    for r in (rows or []):
        rr = dict(r)
        if "enabled" in rr:
            rr["enabled_bool"] = str(rr.get("enabled", "")).strip().lower() in ("true", "1", "yes", "enabled", "on")
        norm_rows.append(rr)

    res["rows"] = norm_rows
    res["count"] = len(norm_rows)
    res["ok"] = True
    return res

# ---------- argparse / main ----------
def main():
    ap = argparse.ArgumentParser(
        description="SSH helper for AWL...id, reboot (with console mute), and pull-log via scp (no sftp)"
    )
    ap.add_argument("--host", required=True)
    ap.add_argument("--user", default=None)
    ap.add_argument("--password", default=None)
    ap.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    ap.add_argument("--bind-src", default=os.environ.get("SSH_BIND_SRC"),help="Bind local source IP (controls which NIC to use). Same as env SSH_BIND_SRC.")
    ap.add_argument("--no-root-fallback", action="store_true")
    ap.add_argument(
        "--cmd",
        choices=["node-id", "awlan-info", "wifi-creds", "reboot", "pull-log", "dns-v4", "dns-v6", "wan-ipv4", "wan-ipv6", "health", "upnp-proc", "upnp-ps", "upnp-log", "uptime", "ping", "metrics", "wan-ipv6-detail", "lla", "iface-mac", "macs", "iface-mac", "macs", "dhcp-reserved", "dhcp-leased", "dhcp", "wifi-vif-state", "wifi-radio-state"],
        default="node-id",
    )

    # wifi-creds options
    ap.add_argument(
        "--which",
        choices=["current", "default", "both"],
        default="both",
        help="For --cmd wifi-creds: select credentials source. default=mf_tool (label), current=ovsh (runtime), both=include both.",
    )

    # DNS options
    ap.add_argument("--domain", default=None, help="Domain name for dns-v4/dns-v6")
    ap.add_argument("--dns-server", default=None, help="DNS server to use on CPE for nslookup (IPv4 or IPv6).")
    ap.add_argument("--dns-server-family", choices=["auto","v4","v6"], default="auto", help="If --dns-server is not set, try to pick a nameserver of this family from /etc/resolv.conf.")


    # UPNP options (for --cmd upnp-log / upnp-ps / upnp-proc)
    ap.add_argument("--lines", type=int, default=int(os.environ.get("UPNP_LOG_LINES","200")),
                    help="Tail N lines from log file for upnp-log (default: 200)")
    ap.add_argument("--grep", dest="grep_word", default=os.environ.get("UPNP_LOG_GREP","upnp"),
                    help="grep keyword for upnp-log (default: upnp)")
    ap.add_argument("--window-min", type=int, default=int(os.environ.get("UPNP_LOG_WINDOW_MIN","30")),
                    help="Time window minutes for upnp-log parsing (default: 30)")
    ap.add_argument("--log-file", dest="upnp_log_file", default=os.environ.get("UPNP_LOG_FILE","/var/log/messages"),
                    help="Log file path for upnp-log (default: /var/log/messages)")
    ap.add_argument("--expect-found", type=int, default=None,
                    help="For upnp-ps/upnp-proc: expect miniupnpd found? 1=yes 0=no. If omitted, pass==found.")

    # iface options
    ap.add_argument("--iface", default="br-wan", help="Interface name for --cmd wan-ipv4/wan-ipv6/lla/iface-mac (default: br-wan)")
    ap.add_argument("--ifaces", default=None, help="Comma-separated interface list for --cmd macs (default: br-wan,br-home,wifi0,wifi1,wifi2)")
    ap.add_argument("--debug", action="store_true", help="Include per-iface raw outputs (attempts/raw) for troubleshooting. Default: off")
    ap.add_argument("--json", action="store_true", help="Output JSON for scalar commands (compat with other tools).")
    
    # ping options
    ap.add_argument("--target", default=None, help="Ping target IP/FQDN when --cmd ping")
    ap.add_argument("--count", type=int, default=4, help="Ping count when --cmd ping (default: 4)")
    # metrics options
    ap.add_argument(
        "--rate-interval",
        type=float,
        default=float(os.environ.get("SSH_METRICS_RATE_INTERVAL_SEC", "1.0")),
        help="Interval seconds for RX/TX rate calculation when --cmd metrics (default: 1.0)",
    )
    ap.add_argument(
        "--latency-target",
        default=os.environ.get("SSH_METRICS_LATENCY_TARGET", None),
        help="Optional ping target to measure latency_ms when --cmd metrics (e.g. 1.1.1.1). If unset, latency_ms may be null.",
    )
    ap.add_argument(
        "--latency-ms",
        type=float,
        default=None,
        help="If provided, use this value for latency_ms (skip probing) when --cmd metrics",
    )

    # console mute for reboot
    ap.add_argument(
        "--mute-console-secs",
        type=int,
        default=int(os.environ.get("SERIAL_MUTE_SEC", "0")),
    )
    ap.add_argument("--mute-with-lock", action="store_true")

    # pull-log options
    ap.add_argument(
        "--src",
        dest="src_list",
        action="append",
        nargs="+",
        help="Remote path(s). Wildcards allowed; expanded via ssh on remote.",
    )
    ap.add_argument(
        "--dest",
        default=".",
        help=f"Local file/dir. When used with --latest-from-dir and left as '.', defaults to {DEFAULT_LOCAL_DEST}",
    )
    ap.add_argument("--recursive", action="store_true")
    ap.add_argument("--latest-from-dir", dest="latest_dir", default=None)
    ap.add_argument("--pattern", default=DEFAULT_LOGPULL_PATTERN)

    # pre logpull
    ap.add_argument("--pre-logpull", dest="pre_logpull", action="store_true")
    ap.add_argument("--no-pre-logpull", dest="pre_logpull", action="store_false")
    ap.set_defaults(pre_logpull=True)
    ap.add_argument(
        "--logpull-timeout", type=int, default=DEFAULT_PRE_LOGPULL_TIMEOUT
    )

    # ssh quiet / rename
    ap.add_argument("--ssh-quiet", dest="ssh_quiet", action="store_true")
    ap.add_argument("--no-ssh-quiet", dest="ssh_quiet", action="store_false")
    ap.set_defaults(ssh_quiet=True)

    ap.add_argument("--rename-with-node-id", dest="rename_nid", action="store_true")
    ap.add_argument(
        "--no-rename-with-node-id", dest="rename_nid", action="store_false"
    )
    ap.set_defaults(rename_nid=True)

    # delete remote after success
    ap.add_argument(
        "--delete-remote",
        action="store_true",
        help="Delete remote file(s) after successful download",
    )

    args = ap.parse_args()
    if args.bind_src:
        os.environ["SSH_BIND_SRC"] = str(args.bind_src)
    root_fallback = not args.no_root_fallback

    # set global ssh loglevel
    global _SSH_LOGLEVEL
    _SSH_LOGLEVEL = "ERROR" if args.ssh_quiet else "INFO"

    # ---------- node-id ----------
    if args.cmd == "node-id":
        nid, meta = get_awlan_node_id(
            args.host,
            user=args.user,
            password=args.password,
            root_fallback=root_fallback,
            timeout=args.timeout,
        )
        if meta.get("ok") and nid:
            if args.json:
                print(json.dumps({"ok": True, "host": args.host, "node_id": nid}, ensure_ascii=False, indent=2))
            else:
                print(nid)
            raise SystemExit(0)
        print(json.dumps(meta, ensure_ascii=False, indent=2))
        raise SystemExit(1)


    # ---------- awlan-info (serial/model/firmware) ----------
    elif args.cmd == "awlan-info":
        info, meta = get_awlan_node_info(
            args.host,
            user=args.user,
            password=args.password,
            root_fallback=root_fallback,
            timeout=args.timeout,
        )
        out = {
            "ok": bool(meta.get("ok")),
            "serial_number": info.get("serial_number"),
            "model": info.get("model"),
            "firmware_version": info.get("firmware_version"),
            "host": args.host,
            "user": meta.get("user"),
            "rc": meta.get("rc"),
            "sec": meta.get("sec"),
        }
        if not out["ok"]:
            out["attempts"] = meta.get("attempts", [])
            out["stderr"] = meta.get("stderr")
        print(json.dumps(out, ensure_ascii=False, indent=2))
        raise SystemExit(0 if out["ok"] else 1)


    # ---------- wifi-creds ----------
    elif args.cmd == "wifi-creds":
        res = get_wifi_creds(
            args.host,
            user=args.user,
            password=args.password,
            root_fallback=root_fallback,
            timeout=args.timeout,
            which=getattr(args, "which", "both"),
        )
        print(json.dumps(res, ensure_ascii=False, indent=2))
        raise SystemExit(0 if res.get("ok") else 1)


    # ---------- wifi-vif-state ----------
    elif args.cmd == "wifi-vif-state":
        res = get_wifi_vif_state(
        args.host,
        user=args.user,
        password=args.password,
        root_fallback=root_fallback,
        timeout=args.timeout,
    )
        print(json.dumps(res, ensure_ascii=False, indent=2))
        raise SystemExit(0 if res.get("ok") else 1)

    # ---------- wifi-radio-state ----------
    elif args.cmd == "wifi-radio-state":
        res = get_wifi_radio_state(
        args.host,
        user=args.user,
        password=args.password,
        root_fallback=root_fallback,
        timeout=args.timeout,
    )
        print(json.dumps(res, ensure_ascii=False, indent=2))
        raise SystemExit(0 if res.get("ok") else 1)


    # ---------- reboot ----------
    elif args.cmd == "reboot":
        if int(args.mute_console_secs or 0) > 0:
            set_console_mute(
                int(args.mute_console_secs),
                use_lock=args.mute_with_lock,
                lock_timeout=5,
            )
        ok, meta = trigger_reboot(
            args.host,
            user=args.user,
            password=args.password,
            root_fallback=root_fallback,
            timeout=args.timeout,
        )
        if ok:
            print("REBOOTING")
            raise SystemExit(0)
        print(json.dumps(meta, ensure_ascii=False, indent=2))
        raise SystemExit(1)

    # ---------- dns-v4 ----------
    elif args.cmd == "dns-v4":
        if not args.domain:
            print(
                json.dumps(
                    {"ok": False, "error": "domain_required"}, ensure_ascii=False
                )
            )
            raise SystemExit(1)
        ips, meta = query_dnsv4(
            args.host,
            args.domain,
            user=args.user,
            password=args.password,
            timeout=args.timeout,
        dns_server=args.dns_server,
            dns_server_family=args.dns_server_family,
        )
        out = {
            "count": meta.get("count", len(ips)),
            "ips": meta.get("ips", ips),
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        raise SystemExit(0 if meta.get("ok") else 1)

    # ---------- dns-v6 ----------
    elif args.cmd == "dns-v6":
        if not args.domain:
            print(
                json.dumps(
                    {"ok": False, "error": "domain_required"}, ensure_ascii=False
                )
            )
            raise SystemExit(1)
        ips, meta = query_dnsv6(
            args.host,
            args.domain,
            user=args.user,
            password=args.password,
            timeout=args.timeout,
        dns_server=args.dns_server,
            dns_server_family=args.dns_server_family,
        )
        out = {
            "count": meta.get("count", len(ips)),
            "ips": meta.get("ips", ips),
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        raise SystemExit(0 if meta.get("ok") else 1)

    # ---------- wan-ipv4 ----------
    elif args.cmd == "wan-ipv4":
        ipv4, meta = get_iface_ipv4(
            args.host,
            iface=(args.iface or "br-wan"),
            user=args.user,
            password=args.password,
            root_fallback=root_fallback,
            timeout=args.timeout,
        )
        if ipv4:
            print(ipv4)
            raise SystemExit(0)
        print(json.dumps(meta, ensure_ascii=False, indent=2))
        raise SystemExit(1)

    
    # ---------- wan-ipv6 ----------
    elif args.cmd == "wan-ipv6":
        ipv6, meta = get_iface_ipv6(
            args.host,
            iface=(args.iface or "br-wan"),
            user=args.user,
            password=args.password,
            root_fallback=root_fallback,
            timeout=args.timeout,
        )
        if ipv6:
            print(ipv6)
            raise SystemExit(0)
        print(json.dumps(meta, ensure_ascii=False, indent=2))
        raise SystemExit(1)

    # ---------- wan-ipv6-detail ----------
    elif args.cmd == "wan-ipv6-detail":
        ipv6, meta = get_iface_ipv6(
            args.host,
            iface=(args.iface or "br-wan"),
            user=args.user,
            password=args.password,
            root_fallback=root_fallback,
            timeout=args.timeout,
        )
        out = {
            "ok": bool(ipv6),
            "host": args.host,
            "iface": (args.iface or "br-wan"),
            "ipv6": meta.get("ipv6"),
            "prefix_len": meta.get("prefix_len"),
            "rc": meta.get("rc"),
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        raise SystemExit(0 if ipv6 else 1)

    # ---------- lla ----------
    elif args.cmd == "lla":
        lla, meta = get_iface_lla_ipv6(
            args.host,
            iface=(args.iface or "br-home"),
            user=args.user,
            password=args.password,
            root_fallback=root_fallback,
            timeout=args.timeout,
        )
        out = {
            "ok": bool(lla),
            "host": args.host,
            "iface": (args.iface or "br-home"),
            "lla": lla,
            "prefix_len": meta.get("prefix_len"),
        }
        if not lla:
            out["meta"] = meta
        print(json.dumps(out, ensure_ascii=False, indent=2))
        raise SystemExit(0 if lla else 1)

    # ---------- iface-mac ----------
    elif args.cmd == "iface-mac":
        mac, meta = get_iface_mac(
            args.host,
            iface=(args.iface or "br-wan"),
            user=args.user,
            password=args.password,
            root_fallback=root_fallback,
            timeout=args.timeout,
        )
        out = {
            "ok": bool(mac),
            "host": args.host,
            "iface": (args.iface or "br-wan"),
            "mac": mac,
        }
        if not mac:
            out["meta"] = meta
        print(json.dumps(out, ensure_ascii=False, indent=2))
        raise SystemExit(0 if mac else 1)

    # ---------- macs ----------
    elif args.cmd == "macs":
        if args.ifaces:
            ifaces = [x.strip() for x in str(args.ifaces).split(",") if x.strip()]
        else:
            ifaces = ["br-wan", "br-home", "wifi0", "wifi1", "wifi2"]

        macs, meta = get_iface_macs(
            args.host,
            ifaces=ifaces,
            user=args.user,
            password=args.password,
            root_fallback=root_fallback,
            timeout=args.timeout,
        )

        # 多介面查詢時，CPE login banner 可能會混入 stdout。解析 MAC 已經不受影響，
        # 但 CLI 預設輸出精簡版，避免把 banner/attempts 全塞進 JSON。
        env_debug = str(os.environ.get("CPE_SSH_DEBUG", "0")).lower() in ("1", "true", "yes")
        debug = bool(args.debug or env_debug)

        out = {
            "ok": bool(meta.get("ok")),
            "host": args.host,
            "count": meta.get("count"),
            "macs": macs,
        }

        missing = [k for k, v in (macs or {}).items() if not v]
        if missing:
            out["missing"] = missing

        if debug:
            out["ifaces"] = meta.get("ifaces")

        print(json.dumps(out, ensure_ascii=False, indent=2))
        raise SystemExit(0 if out.get("ok") else 1)

    # ---------- dhcp (reserved / leased / both) ----------
    elif args.cmd in ("dhcp", "dhcp-reserved", "dhcp-leased"):
        reserved = leased = None
        meta_r = meta_l = None

        if args.cmd in ("dhcp", "dhcp-reserved"):
            reserved, meta_r = get_dhcp_reserved_ips(
                args.host,
                user=args.user,
                password=args.password,
                root_fallback=root_fallback,
                timeout=args.timeout,
            )

        if args.cmd in ("dhcp", "dhcp-leased"):
            leased, meta_l = get_dhcp_leased_ips(
                args.host,
                user=args.user,
                password=args.password,
                root_fallback=root_fallback,
                timeout=args.timeout,
            )

        out = {
            "ok": bool(reserved) if args.cmd == "dhcp-reserved"
                  else bool(leased) if args.cmd == "dhcp-leased"
                  else (bool(reserved) or bool(leased)),
            "host": args.host,
            "reserved_count": len(reserved or []),
            "leased_count": len(leased or []),
            "reserved": reserved or [],
            "leased": leased or [],
            "user_reserved": (meta_r or {}).get("user"),
            "user_leased": (meta_l or {}).get("user"),
        }

        if not out["ok"]:
            out["meta"] = {"reserved": meta_r, "leased": meta_l}

        print(json.dumps(out, ensure_ascii=False, indent=2))
        raise SystemExit(0 if out.get("ok") else 1)


    # ---------- ping ----------
    elif args.cmd == "ping":
        if not args.target:
            print(json.dumps(
                {"ok": False, "error": "target_required"},
                ensure_ascii=False
            ))
            raise SystemExit(1)

        info = ping_from_cpe(
            args.host,
            target=args.target,
            user=args.user,
            password=args.password,
            count=args.count,
            timeout=args.timeout,
        )

        # 只保留你需要的欄位
        out = {
            "ok": bool(info.get("ok")),
            "loss_pct": info.get("loss_pct"),
            # 如果你願意，也可以順便留下這兩個：
            # "sent": info.get("sent"),
            # "received": info.get("received"),
        }

        print(json.dumps(out, ensure_ascii=False, indent=2))
        # 有收到至少 1 個回應就 exit 0，否則 exit 1
        raise SystemExit(0 if out["ok"] else 1)


    # ---------- metrics ----------
    elif args.cmd == "metrics":
        res = collect_basic_metrics(
            args.host,
            iface=args.iface,
            user=args.user,
            password=args.password,
            timeout=args.timeout,
            rate_interval=args.rate_interval,
            latency_target=args.latency_target,
            latency_ms=args.latency_ms,
            root_fallback=root_fallback,
        )
        print(json.dumps(res, ensure_ascii=False, indent=2))
        raise SystemExit(0 if res.get("ok") else 1)

    # ---------- health ----------
    elif args.cmd == "health":
        res = cpe_health_check(
            args.host,
            user=args.user,
            password=args.password,
            timeout=args.timeout,
        )
        print(json.dumps(res, ensure_ascii=False, indent=2))
        # ok=True => exit 0；只要有 FAIL => exit 1
        raise SystemExit(0 if res.get("ok") else 1)
    # ---------- upnp-proc / upnp-ps ----------
    elif args.cmd in ("upnp-proc", "upnp-ps"):
        _, meta = check_upnp_process(
            args.host,
            user=args.user,
            password=args.password,
            timeout=args.timeout,
            expect_found=args.expect_found,
        )
        # 統一用 JSON 輸出，方便腳本 parse
        print(json.dumps(meta, ensure_ascii=False, indent=2))
        # 維持既有語意：exit 0 代表「指令有跑完/可解析」(ok)，不是功能驗證 pass/fail
        raise SystemExit(0 if meta.get("ok") else 1)
    # ---------- upnp-log ----------
    elif args.cmd == "upnp-log":
        meta = check_upnp_logs(
            args.host,
            user=args.user,
            password=args.password,
            timeout=args.timeout,
            log_file=args.upnp_log_file,
            tail_lines=args.lines,
            grep_word=args.grep_word,
            window_min=args.window_min,
        )
        print(json.dumps(meta, ensure_ascii=False, indent=2))
        # 維持既有語意：exit 0 代表「成功拿到/解析 log」(ok)，是否通過驗證請看 meta["pass"]
        raise SystemExit(0 if meta.get("ok") else 1)

    # ---------- uptime ----------
    elif args.cmd == "uptime":
        val, meta = get_cpe_uptime(
            args.host,
            user=args.user,
            password=args.password,
            timeout=args.timeout,
        )
        if val is not None:
            # 只印出 "22 min" 或 "13:38" 這種短字串，方便 script 使用
            print(val)
            raise SystemExit(0)
        # 解析失敗時，把 meta 印出來方便 debug
        print(json.dumps(meta, ensure_ascii=False, indent=2))
        raise SystemExit(1)

    # ---------- pull-log ----------
    elif args.cmd == "pull-log":
        pre_meta = None
        if args.pre_logpull:
            pre_meta = run_logpull(
                args.host,
                args.user
                or _env_any(["SSH_USER", "SSH_USERNAME", "OPERATOR_USER"], "operator"),
                args.password
                or _env_any(
                    ["SSH_PASSWORD", "PASSWORD", "CPE_PASSWORD"], ""
                ),
                timeout=args.logpull_timeout,
            )

        rename_prefix = None
        if args.rename_nid:
            nid, _ = get_awlan_node_id(
                args.host,
                user=args.user,
                password=args.password,
                root_fallback=root_fallback,
                timeout=args.timeout,
            )
            if nid:
                rename_prefix = nid

        if args.latest_dir is not None:
            dest_dir = args.dest if args.dest != "." else DEFAULT_LOCAL_DEST
            ok, meta = pull_latest_log(
                args.host,
                user=args.user,
                password=args.password,
                directory=(args.latest_dir or DEFAULT_LOGPULL_DIR),
                pattern=args.pattern,
                dest_dir=dest_dir,
                timeout=args.timeout,
                rename_prefix=rename_prefix,
                delete_remote=args.delete_remote,
            )
            if pre_meta is not None:
                meta = {"pre": pre_meta, **meta}
            print(json.dumps(meta, ensure_ascii=False, indent=2))
            raise SystemExit(0 if ok else 1)

        flat_src = []
        if args.src_list:
            for group in args.src_list:
                flat_src.extend(group)
        else:
            flat_src = ["/var/log/messages"]

        ok, meta = pull_logs(
            args.host,
            user=args.user,
            password=args.password,
            sources=flat_src,
            dest=args.dest,
            recursive=args.recursive,
            timeout=args.timeout,
            rename_prefix=rename_prefix,
            delete_remote=args.delete_remote,
        )
        if pre_meta is not None:
            meta = {"pre": pre_meta, **meta}
        print(json.dumps(meta, ensure_ascii=False, indent=2))
        raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
