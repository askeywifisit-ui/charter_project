#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rename latest downloaded log file by appending __run_<RUN_ID> to the filename.
- Derives RUN_ID from:
  1) env RUN_ID
  2) current working dir like .../work/run_1449
  3) timestamp fallback
- Prints a structured event line for your GUI log.
- Exits 0 even if no file matched (just logs why), so pipeline不會因此 fail。
"""
from __future__ import annotations
import argparse, glob, os, re, sys, time
from pathlib import Path

def _json(obj: dict):
    # 輕量 event printer
    sys.stdout.write(str(obj).replace("'", '"') + "\n")
    sys.stdout.flush()

def _detect_run_id() -> str:
    # 1) env
    rid = os.environ.get("RUN_ID", "").strip()
    if rid:
        return rid
    # 2) 從 CWD 抓 run_XXXX
    cwd = Path.cwd()
    m = re.search(r"run_(\d+)", cwd.name)
    if not m:
        # 再往上一層找
        for p in cwd.parents:
            m = re.search(r"run_(\d+)", p.name)
            if m:
                break
    if m:
        return m.group(1)
    # 3) 退而求其次：時間戳
    return time.strftime("%Y%m%d%H%M%S")

def _add_runid(name: str, run_id: str) -> str:
    # *.tar.gz 要在 .tar.gz 前插入
    if name.endswith(".tar.gz"):
        root = name[:-7]  # 去掉 .tar.gz
        return f"{root}__run_{run_id}.tar.gz"
    root, ext = os.path.splitext(name)
    return f"{root}__run_{run_id}{ext}"

def _rename(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.resolve() == dst.resolve():
        return
    os.replace(src, dst)

def rename_latest(dest_dir: Path, pattern: str, run_id: str, exact_file: Path | None = None) -> tuple[bool, str, str]:
    """回傳 (ok, src, dst)。若沒找到，ok=False，src/dst 可能為空字串。"""
    if exact_file:
        src = exact_file
        if not src.exists():
            _json({"step":"logpull-rename","ok":False,"reason":"exact_file_not_found","file":str(src),"run_id":run_id})
            return False, "", ""
    else:
        matches = sorted(dest_dir.glob(pattern), key=lambda p: p.stat().st_mtime if p.exists() else 0)
        if not matches:
            _json({"step":"logpull-rename","ok":False,"reason":"no_match","dest":str(dest_dir),"pattern":pattern,"run_id":run_id})
            return False, "", ""
        src = matches[-1]

    # 已經加過 run_id 就跳過
    if f"__run_{run_id}" in src.name:
        _json({"step":"logpull-rename","ok":True,"skipped":"already_tagged","path":str(src),"run_id":run_id})
        return True, str(src), str(src)

    dst = src.with_name(_add_runid(src.name, run_id))
    _rename(src, dst)
    _json({"step":"logpull-rename","ok":True,"src":str(src),"dst":str(dst),"run_id":run_id})
    return True, str(src), str(dst)

def main():
    ap = argparse.ArgumentParser(description="Append __run_<RUN_ID> to the newest log file name.")
    ap.add_argument("--dest", required=True, help="Logs directory (e.g., /home/da40/charter/logs/cpe)")
    ap.add_argument("--pattern", default="*.tar.gz", help='Glob pattern under --dest (default: "*.tar.gz")')
    ap.add_argument("--file", help="Exact file path to rename instead of searching by pattern")
    ap.add_argument("--run-id", help="Override run id (default: auto-detect from CWD or env RUN_ID)")
    args = ap.parse_args()

    run_id = (args.run_id or _detect_run_id()).strip()
    dest_dir = Path(args.dest)
    exact = Path(args.file) if args.file else None

    _json({"step":"run-context","cwd":str(Path.cwd()),"run_id":run_id})
    ok, _, _ = rename_latest(dest_dir, args.pattern, run_id, exact_file=exact)
    sys.exit(0 if ok else 0)

if __name__ == "__main__":
    main()

