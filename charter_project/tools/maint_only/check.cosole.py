#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
C00000003_console.py

目的：
  只驗證「console serial port 能不能用帳號/密碼登入，並成功執行一個指令」。

實作方式：
  - 透過 /home/da40/charter/tools/cpe_metrics_agent_serial.py
  - 預設執行指令：node-id
  - 成功取得非空輸出 → 視為 PASS（exit 0）
  - 否則視為 FAIL（exit 1）

可由環境變數或參數調整：
  環境變數：
    CPE_DEV        預設 /dev/ttyUSB0
    CPE_BAUD       預設 115200
    CPE_USER       預設 root
    CPE_PASSWORD   預設空字串（會當成 'null' 丟進 metrics_tool，讓它自己決定）
    CONSOLE_CMD    預設 node-id
    METRICS_TOOL   預設 /home/da40/charter/tools/cpe_metrics_agent_serial.py
    MAX_RETRIES    預設 3
    RETRY_INTERVAL_SEC 預設 2

  參數（優先於環境）：
    --device DEV
    --baud N
    --user NAME
    --password PW
    --cmd CMD
    --metrics-tool PATH
"""

import os
import sys
import json
import time
import subprocess
from typing import List, Optional

CPE_DEV="/dev/serial/by-id/usb-ASKEY_ASKEY_Console_Board_FT4PGJN6-if02-port0"
CPE_BAUD=115200
CPE_USER="root"
CPE_PASSWORD="E1G5Q000092"   # 或空白，讓 cpe_metrics_agent_serial 去抓


def getenv(name: str, default: str) -> str:
    return os.environ.get(name, default) or default


def jlog(event: str, **kw) -> None:
    rec = {
        "event": event,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
    }
    rec.update(kw)
    print(json.dumps(rec, ensure_ascii=False), flush=True)


def parse_args(argv):
    """
    非常簡單的手刻 parser，參數優先於環境變數。
    """
    dev = None
    baud = None
    user = None
    password = None
    cmd = None
    metrics_tool = None

    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--device" and i + 1 < len(argv):
            dev = argv[i + 1]
            i += 2
        elif a == "--baud" and i + 1 < len(argv):
            baud = argv[i + 1]
            i += 2
        elif a == "--user" and i + 1 < len(argv):
            user = argv[i + 1]
            i += 2
        elif a == "--password" and i + 1 < len(argv):
            password = argv[i + 1]
            i += 2
        elif a == "--cmd" and i + 1 < len(argv):
            cmd = argv[i + 1]
            i += 2
        elif a == "--metrics-tool" and i + 1 < len(argv):
            metrics_tool = argv[i + 1]
            i += 2
        elif a in ("-h", "--help"):
            print(__doc__ or "")
            sys.exit(0)
        else:
            # 忽略未知參數
            i += 1

    return {
        "dev": dev,
        "baud": baud,
        "user": user,
        "password": password,
        "cmd": cmd,
        "metrics_tool": metrics_tool,
    }


def run_console_check(
    metrics_tool: str,
    dev: str,
    baud: int,
    user: str,
    password: Optional[str],
    cmd_name: str,
) -> bool:
    """
    呼叫 cpe_metrics_agent_serial.py，確認能透過 console 執行 cmd_name。

    回傳 True 表示成功（有非空輸出），False 表示失敗。
    """
    # 讀 retry 設定
    try:
        max_retries = int(getenv("MAX_RETRIES", "3"))
    except Exception:
        max_retries = 3
    try:
        retry_interval = float(getenv("RETRY_INTERVAL_SEC", "2"))
    except Exception:
        retry_interval = 2.0

    last_error: Optional[BaseException] = None

    for attempt in range(1, max_retries + 1):
        # 準備命令列
        cmd: List[str] = [
            metrics_tool,
            "--device",
            dev,
            "--baud",
            str(baud),
            "--user",
            user,
            "--cmd",
            cmd_name,
        ]

        # 處理密碼：
        # - 如果 password 是空白 / None，就丟 'null' 給 metrics_tool，讓它跟 cpe_info 配合
        # - 否則直接用提供的密碼
        if password is None or password == "":
            cmd += ["--password", "null"]
            pw_for_log = "null"
        else:
            cmd += ["--password", password]
            pw_for_log = "***"  # log 不曝光明碼

        jlog(
            "console-node-id-cmd",
            attempt=attempt,
            max_retries=max_retries,
            metrics_tool=metrics_tool,
            dev=dev,
            baud=baud,
            user=user,
            cmd_name=cmd_name,
            password=pw_for_log,
            argv=cmd,
        )

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60.0,
            )
        except Exception as e:
            last_error = e
            jlog(
                "console-node-id-exception",
                attempt=attempt,
                error=str(e),
            )
            time.sleep(retry_interval)
            continue

        out = (proc.stdout or "").strip()
        err = (proc.stderr or "").strip()

        jlog(
            "console-node-id-raw",
            attempt=attempt,
            rc=proc.returncode,
            out=out[-400:],
            err=err[-400:],
        )

        if proc.returncode != 0:
            last_error = RuntimeError(f"rc={proc.returncode}")
            jlog(
                "console-node-id-attempt-failed",
                attempt=attempt,
                error=f"metrics_tool rc={proc.returncode}",
            )
            time.sleep(retry_interval)
            continue

        # 找第一行非空白的輸出
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            jlog(
                "console-node-id-ok",
                attempt=attempt,
                line=line,
            )
            # 只要有一行非空白，就當作「登入 + 指令成功」
            return True

        # 沒抓到任何內容，視為失敗重試
        last_error = RuntimeError("no non-empty output")
        jlog(
            "console-node-id-attempt-failed",
            attempt=attempt,
            error="no non-empty output",
        )
        time.sleep(retry_interval)

    # 全部重試都失敗
    jlog(
        "console-node-id-failed",
        error=str(last_error) if last_error else "unknown",
    )
    return False


def main(argv=None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    args = parse_args(argv)

    dev = args["dev"] or getenv("CPE_DEV", "/dev/ttyUSB0")
    baud_str = args["baud"] or getenv("CPE_BAUD", "115200")
    user = args["user"] or getenv("CPE_USER", "root")
    password = args["password"]
    cmd_name = args["cmd"] or getenv("CONSOLE_CMD", "node-id")
    metrics_tool = args["metrics_tool"] or getenv(
        "METRICS_TOOL", "/home/da40/charter/tools/cpe_metrics_agent_serial.py"
    )

    try:
        baud = int(baud_str)
    except Exception:
        baud = 115200

    jlog(
        "console-check-start",
        dev=dev,
        baud=baud,
        user=user,
        cmd_name=cmd_name,
        metrics_tool=metrics_tool,
    )

    ok = run_console_check(
        metrics_tool=metrics_tool,
        dev=dev,
        baud=baud,
        user=user,
        password=password,
        cmd_name=cmd_name,
    )

    jlog("console-check-result", ok=ok)

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

