#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ssh_awlan_tool.py — SSH helper for querying AWLAN_Node.id + safe reboot
with optional serial-console mute before reboot (compatible with your serial_mute/serial_lock).

Usage:
  # 查 AWLAN_Node.id
  python3 ssh_awlan_tool.py --host 192.168.1.1 --user operator --password 1234 --cmd node-id

  # 觸發 CPE 重開機（先把 console 靜音 120 秒，設定靜音時加鎖）
  python3 ssh_awlan_tool.py --host 192.168.1.1 --user operator --password 1234 \
    --cmd reboot --mute-console-secs 120 --mute-with-lock

Env:
  SSH_USER / SSH_USERNAME / OPERATOR_USER
  SSH_PASSWORD / PASSWORD / CPE_PASSWORD
  SSH_USER_LAN_FALLBACK (default: root)
  SSH_REBOOT_CMD           # 覆寫 reboot 指令鏈
  SERIAL_MUTE_SEC          # --mute-console-secs 預設值
  SERIAL_MUTE_FILE         # 無 serial_mute 模組時的旗標檔路徑 (default: /home/da40/charter/var/serial.mute)

Exit:
  node-id 成功 -> 印出 node id，exit 0；失敗 -> 印 JSON，exit 1
  reboot  成功 -> 印出 "REBOOTING"，exit 0；失敗 -> 印 JSON，exit 1

Requires: paramiko
"""
import os
import re
import time
import json
import argparse
import contextlib

import paramiko

# ---------- defaults ----------
DEFAULT_TIMEOUT = float(os.environ.get("SSH_TIMEOUT_SEC", "10"))
LOGIN_SHELL = os.environ.get("SSH_LOGIN_SHELL", "sh -lc").strip()

# ---------- optional deps from your repo ----------
try:
    # 你現有的 serial_lock.py，提供 acquire(block=True, timeout=...)
    from serial_lock import acquire as serial_lock_acquire  # context manager
except Exception:
    serial_lock_acquire = None

try:
    # 你現有的 serial_mute.py，提供 mute_for(secs), left_seconds(), clear()
    import serial_mute
except Exception:
    serial_mute = None

# ---------- helpers ----------
def _env_any(names, default=None):
    for n in names:
        v = os.environ.get(n)
        if v not in (None, ""):
            return v
    return default

def _connect(host, user, password, timeout=DEFAULT_TIMEOUT):
    t0 = time.time()
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(
        hostname=host,
        username=user,
        password=password,
        timeout=timeout,
        banner_timeout=timeout,
        auth_timeout=timeout,
        look_for_keys=False,
        allow_agent=False,
    )
    return cli, t0

def ssh_exec(host, user, password, cmd, *, timeout=DEFAULT_TIMEOUT, login_shell=True):
    """
    Execute a command remotely and return (rc, out, err, sec)
    """
    cli, t0 = _connect(host, user, password, timeout=timeout)
    try:
        to_run = f'{LOGIN_SHELL} "{cmd}"' if login_shell else cmd
        stdin, stdout, stderr = cli.exec_command(to_run, timeout=timeout)
        out_txt = stdout.read().decode("utf-8", errors="ignore").strip()
        err_txt = stderr.read().decode("utf-8", errors="ignore").strip()
        rc = stdout.channel.recv_exit_status()
        return rc, out_txt, err_txt, round(time.time() - t0, 3)
    finally:
        try:
            cli.close()
        except Exception:
            pass

OVSH_CHAIN = (
    "([ -x /usr/opensync/tools/ovsh ] && /usr/opensync/tools/ovsh {args})"
    " || "
    "([ -x /usr/opensync/bin/ovsh ] && /usr/opensync/bin/ovsh {args})"
    " || "
    "(ovsh {args})"
)

ID_PAT = re.compile(r'\b([0-9a-f]{10,})\b', re.I)

def _parse_node_id(text: str) -> str:
    for line in (text or "").splitlines():
        m = re.search(r'\bid\s*[:=]\s*([0-9a-f]{10,})\b', line, re.I)
        if m:
            return m.group(1).lower()
    m = ID_PAT.search(text or "")
    return m.group(1).lower() if m else (text or "").strip()

def get_awlan_node_id(host: str, *, user: str = None, password: str = None,
                      root_fallback: bool = True, timeout: float = DEFAULT_TIMEOUT):
    """
    Returns (node_id, meta_dict) — meta includes rc/out/err/user/duration/cmd_used.
    """
    user = user or _env_any(["SSH_USER", "SSH_USERNAME", "OPERATOR_USER"], "operator")
    password = password or _env_any(["SSH_PASSWORD", "PASSWORD", "CPE_PASSWORD"], "")
    root_user = os.environ.get("SSH_USER_LAN_FALLBACK", "root")
    root_pass = _env_any(["CPE_PASSWORD", "CPE_PASS", "SSH_ROOT_PASSWORD"], password)

    attempts = []
    cmds = [
        OVSH_CHAIN.format(args="s -r AWLAN_Node -c id 2>/dev/null"),
        OVSH_CHAIN.format(args="s AWLAN_Node id 2>/dev/null"),
    ]

    for cmd in cmds:
        rc, out, err, sec = ssh_exec(host, user, password, cmd, timeout=timeout, login_shell=True)
        attempts.append({"user": user, "cmd": cmd, "rc": rc, "sec": sec, "out": out[:200], "err": err[:200]})
        txt = (out or "") + "\n" + (err or "")
        nid = _parse_node_id(txt)
        if nid:
            return nid, {"ok": True, "user": user, "rc": rc, "sec": sec, "cmd": cmd, "out": out, "err": err, "attempts": attempts}

    if root_fallback and user != root_user:
        for cmd in cmds:
            rc, out, err, sec = ssh_exec(host, root_user, root_pass, cmd, timeout=timeout, login_shell=True)
            attempts.append({"user": root_user, "cmd": cmd, "rc": rc, "sec": sec, "out": out[:200], "err": err[:200]})
            txt = (out or "") + "\n" + (err or "")
            nid = _parse_node_id(txt)
            if nid:
                return nid, {"ok": True, "user": root_user, "rc": rc, "sec": sec, "cmd": cmd, "out": out, "err": err, "attempts": attempts}

    last = attempts[-1] if attempts else {}
    return "", {"ok": False, "user": last.get("user"), "rc": last.get("rc"), "sec": last.get("sec"),
                "cmd": last.get("cmd"), "out": last.get("out"), "err": last.get("err"), "attempts": attempts}

def _reboot_chain():
    custom = os.environ.get("SSH_REBOOT_CMD")
    if custom and custom.strip():
        return custom.strip()
    # echo REBOOTING 讓呼叫端能得到 rc=0 與標記字樣；sleep 1 再重啟避免立即斷線造成誤判
    return "nohup sh -c 'sleep 1; (reboot || /sbin/reboot || busybox reboot || systemctl reboot)' >/dev/null 2>&1 & echo REBOOTING"

def trigger_reboot(host: str, *, user: str = None, password: str = None,
                   root_fallback: bool = True, timeout: float = DEFAULT_TIMEOUT):
    """
    Returns (ok, meta_dict). Prints 'REBOOTING' on success in main().
    """
    user = user or _env_any(["SSH_USER", "SSH_USERNAME", "OPERATOR_USER"], "operator")
    password = password or _env_any(["SSH_PASSWORD", "PASSWORD", "CPE_PASSWORD"], "")
    root_user = os.environ.get("SSH_USER_LAN_FALLBACK", "root")
    root_pass = _env_any(["CPE_PASSWORD", "CPE_PASS", "SSH_ROOT_PASSWORD"], password)

    attempts = []
    cmd = _reboot_chain()

    rc, out, err, sec = ssh_exec(host, user, password, cmd, timeout=timeout, login_shell=True)
    attempts.append({"user": user, "cmd": cmd, "rc": rc, "sec": sec, "out": out[:200], "err": err[:200]})
    if rc == 0 and ("REBOOTING" in (out or "").upper() or out.strip().upper() == "REBOOTING"):
        return True, {"ok": True, "user": user, "rc": rc, "sec": sec, "cmd": cmd, "out": out, "err": err, "attempts": attempts}

    if root_fallback and user != root_user:
        rc, out, err, sec = ssh_exec(host, root_user, root_pass, cmd, timeout=timeout, login_shell=True)
        attempts.append({"user": root_user, "cmd": cmd, "rc": rc, "sec": sec, "out": out[:200], "err": err[:200]})
        if rc == 0 and ("REBOOTING" in (out or "").upper() or out.strip().upper() == "REBOOTING"):
            return True, {"ok": True, "user": root_user, "rc": rc, "sec": sec, "cmd": cmd, "out": out, "err": err, "attempts": attempts}

    last = attempts[-1]
    if ("connection reset" in (last.get("err") or "").lower()
        or "connection closed" in (last.get("err") or "").lower()):
        return True, {"ok": True, "user": last.get("user"), "rc": last.get("rc"), "sec": last.get("sec"),
                      "cmd": last.get("cmd"), "out": last.get("out"), "err": last.get("err"),
                      "note": "SSH closed during reboot; assuming success", "attempts": attempts}

    return False, {"ok": False, "user": last.get("user"), "rc": last.get("rc"), "sec": last.get("sec"),
                   "cmd": last.get("cmd"), "out": last.get("out"), "err": last.get("err"), "attempts": attempts}

# ---------- serial mute integration ----------
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
    """
    Set serial-console mute window using your existing mechanism.
    Prefer serial_mute.mute_for(); fallback to writing SERIAL_MUTE_FILE.
    """
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
        # fallback: write flag file directly
        _write_mute_file(until_ts)
        return until_ts

# ---------- cli ----------
def main():
    ap = argparse.ArgumentParser(description="SSH helper for AWLAN_Node.id and reboot (with console mute)")
    ap.add_argument("--host", required=True)
    ap.add_argument("--user", default=None)
    ap.add_argument("--password", default=None)
    ap.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    ap.add_argument("--no-root-fallback", action="store_true")
    ap.add_argument("--cmd", choices=["node-id", "reboot"], default="node-id",
                    help="node-id: query AWLAN_Node.id; reboot: trigger device reboot")

    # console mute options (for reboot)
    ap.add_argument("--mute-console-secs", type=int,
                    default=int(os.environ.get("SERIAL_MUTE_SEC", "0")),
                    help="Before reboot, mute serial console for N seconds (0=disable)")
    ap.add_argument("--mute-with-lock", action="store_true",
                    help="Acquire serial lock briefly when setting mute (recommended)")

    args = ap.parse_args()
    root_fallback = (not args.no_root_fallback)

    if args.cmd == "node-id":
        nid, meta = get_awlan_node_id(args.host, user=args.user, password=args.password,
                                      root_fallback=root_fallback, timeout=args.timeout)
        if meta.get("ok") and nid:
            print(nid)
            raise SystemExit(0)
        else:
            print(json.dumps(meta, ensure_ascii=False, indent=2))
            raise SystemExit(1)

    elif args.cmd == "reboot":
        # 1) set mute BEFORE sending reboot
        mute_secs = int(args.mute_console_secs or 0)
        if mute_secs > 0:
            set_console_mute(mute_secs, use_lock=args.mute_with_lock, lock_timeout=5)

        # 2) then trigger reboot via SSH
        ok, meta = trigger_reboot(args.host, user=args.user, password=args.password,
                                  root_fallback=root_fallback, timeout=args.timeout)
        if ok:
            print("REBOOTING")
            raise SystemExit(0)
        else:
            print(json.dumps(meta, ensure_ascii=False, indent=2))
            raise SystemExit(1)

if __name__ == "__main__":
    main()

