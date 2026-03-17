#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
from pathlib import Path
import time, os, argparse, sys

VAR_DIR = Path("/home/da40/charter/var")
FLAG    = VAR_DIR / "serial.mute"

def _set_perms(p: Path):
    try:
        os.chmod(p, 0o664)  # 保證群組可寫
    except Exception:
        pass

def _atomic_write_text(path: Path, text: str) -> None:
    """Write file atomically to avoid partial reads."""
    VAR_DIR.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text)
    _set_perms(tmp)
    os.replace(tmp, path)  # atomic on POSIX
    _set_perms(path)

def _read_until() -> int:
    try:
        s = FLAG.read_text().strip()
        if not s:
            return 0
        # 允許 '1765973245\n' 或 '1765973245.0'
        return int(float(s))
    except FileNotFoundError:
        return 0
    except Exception:
        # 壞檔：清掉，避免留下奇怪狀態
        try:
            FLAG.unlink(missing_ok=True)
        except Exception:
            pass
        return 0

def mute_for(secs: int) -> int:
    secs = int(secs)
    if secs <= 0:
        clear()
        return 0
    until = int(time.time()) + secs
    _atomic_write_text(FLAG, str(until))
    return until

def left_seconds(now: int | None = None) -> int:
    now_i = int(time.time()) if now is None else int(now)
    until = _read_until()
    return max(0, until - now_i)

def is_muted(now: int | None = None) -> bool:
    return left_seconds(now) > 0

def clear() -> None:
    try:
        FLAG.unlink(missing_ok=True)  # 取消靜默
    except Exception:
        pass

def _cli():
    ap = argparse.ArgumentParser(description="Global serial mute flag helper")
    # 相容：舊式子命令（left/get/clear/set）
    ap.add_argument("cmd", nargs="?", choices=["set", "get", "left", "clear"], help="Command mode (compat)")
    ap.add_argument("value", nargs="?", type=int, help="Seconds for set (compat)")

    # 你原本的 flags（保留）
    ap.add_argument("--set", dest="set_secs", type=int, help="Set mute seconds (e.g. 90)")
    ap.add_argument("--get", action="store_true", help="Print seconds left")
    ap.add_argument("--clear", action="store_true", help="Clear mute")
    ns = ap.parse_args()

    # flags 優先
    if ns.set_secs is not None:
        print(mute_for(ns.set_secs))
        return
    if ns.get:
        print(left_seconds())
        return
    if ns.clear:
        clear()
        print(0)
        return

    # compat 子命令
    if ns.cmd == "set":
        if ns.value is None:
            ap.error("set requires seconds, e.g. serial_mute.py set 90")
        print(mute_for(ns.value))
    elif ns.cmd in ("get", "left"):
        print(left_seconds())
    elif ns.cmd == "clear":
        clear()
        print(0)
    else:
        ap.print_help()

if __name__ == "__main__":
    _cli()

