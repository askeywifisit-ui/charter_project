#!/usr/bin/env python3
"""Sync exported script zips from 11F_140 Charter platform and update docs script-id mapping.

- Downloads /api/scripts list from CHARTER_BASE (default 11F_140: http://172.14.1.140:5173)
- For suites sanity/stability: exports each script as zip and writes to scripts/<suite>/<name>.zip
- Runs sanitize_manifests_in_zips.py afterwards (placeholders, no cleartext creds)
- Updates docs markdown files under docs/charter_site/docs/test_suites/** to reflect latest 11F_140 script id.

Usage:
  python3 scripts/sync_scripts_from_11F_140.py

Env:
  CHARTER_BASE (default: http://172.14.1.140:5173)
  LIMIT (default: 2000)
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

CHARTER_BASE = os.environ.get("CHARTER_BASE", "http://172.14.1.140:5173").rstrip("/")
LIMIT = int(os.environ.get("LIMIT", "2000"))
SUITES = {"sanity", "stability"}

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
DOCS_DIR = ROOT / "docs" / "charter_site" / "docs" / "test_suites"

SCRIPT_ID_LINE_RE = re.compile(
    r"^(?P<prefix>\s*-\s*Script ID（可能因 delete/import 變動）：`11F_131=\d+`\s*/\s*`11F_140=)(?P<id>\d+)(?P<suffix>`\s*)$"
)


def http_get_json(url: str):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = r.read()
    return json.loads(data)


def http_download(url: str, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    out_path.write_bytes(data)


def main() -> int:
    scripts_url = f"{CHARTER_BASE}/api/scripts?limit={LIMIT}"
    scripts = http_get_json(scripts_url)
    if not isinstance(scripts, list):
        raise RuntimeError(f"Unexpected response from {scripts_url}")

    # Sync zips
    synced = 0
    by_name_suite: dict[tuple[str, str], int] = {}
    for s in scripts:
        suite = s.get("suite")
        name = s.get("name")
        sid = s.get("id")
        if suite not in SUITES:
            continue
        if not name or not isinstance(sid, int):
            continue

        by_name_suite[(suite, name)] = sid

        out_zip = SCRIPTS_DIR / suite / f"{name}.zip"
        export_url = f"{CHARTER_BASE}/api/scripts/{sid}/export"
        http_download(export_url, out_zip)
        synced += 1

    print(f"[OK] synced zips: {synced}")

    # Sanitize manifests in zips
    sanitize = ROOT / "scripts" / "sanitize_manifests_in_zips.py"
    if sanitize.exists():
        subprocess.check_call([sys.executable, str(sanitize)], cwd=str(ROOT))
        print("[OK] sanitized zip manifests")

    # Update docs script IDs (11F_140)
    updated_files = 0
    for md in DOCS_DIR.glob("**/*.md"):
        rel = md.relative_to(DOCS_DIR)
        # rel like sanity/<name>.md
        try:
            suite = rel.parts[0]
        except Exception:
            continue
        if suite not in SUITES:
            continue
        name = md.stem
        key = (suite, name)
        if key not in by_name_suite:
            continue
        new_id = str(by_name_suite[key])

        lines = md.read_text(encoding="utf-8", errors="ignore").splitlines(True)
        out = []
        changed = False
        for line in lines:
            m = SCRIPT_ID_LINE_RE.match(line.rstrip("\n"))
            if m:
                cur_id = m.group("id")
                if cur_id != new_id:
                    out.append(f"{m.group('prefix')}{new_id}{m.group('suffix')}\n")
                    changed = True
                else:
                    out.append(line)
                continue
            out.append(line)

        if changed:
            md.write_text("".join(out), encoding="utf-8")
            updated_files += 1

    print(f"[OK] updated docs files (11F_140 script id): {updated_files}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
