#!/usr/bin/env python3
import os
import time
import fcntl
import contextlib
import sys
import json

LOCK_PATH = os.environ.get("SERIAL_LOCK_PATH", "/home/da40/charter/var/serial.lock")
os.makedirs(os.path.dirname(LOCK_PATH), exist_ok=True)

def _log(obj: dict):
    # 預設不輸出；避免干擾任何抓 stdout 解析的呼叫端
    if os.environ.get("SERIAL_LOCK_LOG", "0") != "1":
        return
    try:
        sys.stderr.write(json.dumps(obj, ensure_ascii=False) + "\n")
        sys.stderr.flush()
    except Exception:
        pass

@contextlib.contextmanager
def acquire(block: bool = True, timeout: float | None = None):
    """取用序列埠互斥鎖；block=False 取不到會丟 BlockingIOError。"""
    fd = os.open(LOCK_PATH, os.O_CREAT | os.O_RDWR, 0o666)

    t0 = time.monotonic()   # 開始等待拿鎖時間
    t_got = None            # 真正拿到鎖的時間點

    try:
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | (0 if block else fcntl.LOCK_NB))
                t_got = time.monotonic()
                _log({
                    "event": "serial_lock_acquired",
                    "lock": LOCK_PATH,
                    "wait_ms": int((t_got - t0) * 1000),
                })
                break
            except BlockingIOError:
                if not block:
                    raise
                if timeout is not None and (time.monotonic() - t0) >= timeout:
                    raise TimeoutError("serial lock timeout")
                time.sleep(0.1)

        yield

    finally:
        t_end = time.monotonic()
        if t_got is not None:
            _log({
                "event": "serial_lock_released",
                "lock": LOCK_PATH,
                "held_ms": int((t_end - t_got) * 1000),
            })

        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        except Exception:
            pass
        os.close(fd)

