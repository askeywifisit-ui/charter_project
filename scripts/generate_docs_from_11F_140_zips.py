#!/usr/bin/env python3
"""Generate/refresh docs pages for each test case based on latest 11F_140 exported zips.

Inputs:
- scripts/sanity/*.zip and scripts/stability/*.zip (must contain manifest.yaml)
- 11F_140 API list: CHARTER_BASE (default http://172.14.1.140:5173) to map name->script id

Outputs:
- docs/charter_site/docs/test_suites/<suite>/<name>.md

Rules:
- DO NOT publish secrets. Any key that looks sensitive is rendered as <fill>.
- Keep format consistent across pages.

Usage:
  python3 scripts/generate_docs_from_11F_140_zips.py

Env:
  CHARTER_BASE (default http://172.14.1.140:5173)
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import textwrap
import urllib.request
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
DOCS_OUT = ROOT / "docs" / "charter_site" / "docs" / "test_suites"

CHARTER_BASE = os.environ.get("CHARTER_BASE", "http://172.14.1.140:5173").rstrip("/")

SENSITIVE_KEY_PAT = re.compile(
    r"(PASSWORD|PASSWD|TOKEN|SECRET|API_KEY|BEARER|AUTH|EMAIL)", re.IGNORECASE
)

# Some keys are safe even if they match (e.g., ENABLE_*). Keep it simple: only scrub values, keep keys.

def _is_sensitive_key(k: str) -> bool:
    return bool(SENSITIVE_KEY_PAT.search(k))


def _scrub_value(k: str, v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        # allow numeric values even for sensitive keys? safer to scrub if key sensitive.
        return "<fill>" if _is_sensitive_key(k) else v
    if isinstance(v, bool):
        return v
    s = str(v)
    if _is_sensitive_key(k):
        # keep empty/null as-is
        if s.strip() in ("", "null", "None", "<fill>"):
            return s
        return "<fill>"
    # scrub any accidental charter.com in non-sensitive keys
    if "@" in s and "charter.com" in s:
        return "<fill>"
    return v


def _load_script_id_map() -> dict[tuple[str, str], int]:
    url = f"{CHARTER_BASE}/api/scripts?limit=5000"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
    m = {}
    for s in data:
        suite = s.get("suite")
        name = s.get("name")
        sid = s.get("id")
        if suite and name and isinstance(sid, int):
            m[(suite, name)] = sid
    return m


def _read_manifest(zip_path: Path) -> dict:
    with zipfile.ZipFile(zip_path, "r") as z:
        raw = z.read("manifest.yaml").decode("utf-8", "ignore")
    doc = yaml.safe_load(raw) or {}
    if not isinstance(doc, dict):
        raise RuntimeError(f"manifest.yaml not a mapping: {zip_path}")
    return doc


def _yaml_dump_block(obj: dict) -> str:
    # stable-ish yaml
    return yaml.safe_dump(
        obj,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        width=120,
    ).rstrip()


def _make_page(suite: str, name: str, script_id_140: int | None, manifest: dict) -> str:
    version = manifest.get("version", "")
    entrypoint = manifest.get("entrypoint", "")
    env = manifest.get("env") or {}
    if not isinstance(env, dict):
        env = {}

    # scrub env
    env_scrubbed = {}
    for k, v in env.items():
        env_scrubbed[k] = _scrub_value(str(k), v)

    # Key env quick list (top 12, prefer common ones)
    preferred = [
        "TOOLS_PATH",
        "PROFILES_FILE",
        "NOC_PROFILE",
        "CUSTOMER_ID",
        "CPE_HOST",
        "SSH_USER",
        "SSH_PASSWORD",
        "LAN_PARENT_IFACE",
        "WIFI_IFACE",
        "PING_IFACE",
        "CPE_DEV",
        "TEST_PROFILE",
    ]
    key_env_lines = []
    for k in preferred:
        if k in env_scrubbed:
            key_env_lines.append(f"- `{k}`: `{env_scrubbed[k]}`")

    now = _dt.datetime.now().strftime("%Y-%m-%d")
    sid_line = f"`11F_140={script_id_140}`" if script_id_140 else "（尚未對應）"

    header = f"# {name}\n\n- Suite: **{suite}**\n- Script ID（可能因 delete/import 變動）：{sid_line}\n- 版本（manifest version）：`{version}`\n- Entrypoint：`{entrypoint}`\n\n> 本頁由工具依 11F_140 最新 export zip 自動產生/更新（{now}）。\n"

    body = "\n".join(
        [
            "\n## 目的（Purpose）\n",
            "（以腳本內實作為準；此頁主要提供快速落地的安裝/執行資訊。）\n",
            "\n## 前置條件（Preconditions）\n",
            "- 平台服務需正常（web/api/worker）\n- tools 需可用（`/home/da40/charter/tools`）\n",
            "\n## 需依環境替換（給外部單位）\n",
            "以下參數通常因環境而異（請用 Environment Template / `.secrets` 注入）：\n",
            "- `PROFILES_FILE` / `NOC_PROFILE` / `CUSTOMER_ID`\n- `CPE_HOST` / `LAN_PARENT_IFACE` / `WIFI_IFACE` / `PING_IFACE`\n- 任何 `*_PASSWORD` / `*_EMAIL` 一律不得寫死（用 `<fill>` 或 secrets）\n",
            "\n## Key env quick reference\n",
            ("\n".join(key_env_lines) + "\n") if key_env_lines else "（無）\n",
            "\n## manifest.yaml（節錄：env）\n",
            "```yaml\n" + _yaml_dump_block({"name": name, "suite": suite, "version": version, "entrypoint": entrypoint, "env": env_scrubbed}) + "\n```\n",
            "\n## Run（建議 API 方式）\n",
            "```bash\nexport CHARTER_BASE=\"http://<CONTROL_PC_IP>:5173\"\nSCRIPT_ID=<SCRIPT_ID_11F_140>\ncurl -sS -X POST \"$CHARTER_BASE/api/scripts/$SCRIPT_ID/run\" | python3 -m json.tool\n```\n",
            "\n## Artifacts / Evidence\n",
            "```bash\nRID=<RUN_ID>\ncurl -sS \"$CHARTER_BASE/api/runs/$RID/log\" > run_${RID}_log.json\ncurl -sS \"$CHARTER_BASE/api/runs/$RID/log-archives\" | python3 -m json.tool\n# 若有 log archive：\ncurl -fsSL \"$CHARTER_BASE/api/runs/$RID/log-archive\" -o run_${RID}_cpe_log.tar.gz\n```\n",
            "\n## Cleanup\n",
            "```bash\ncurl -sS -X DELETE \"$CHARTER_BASE/api/runs/purge?older_than_days=0\" | python3 -m json.tool\n```\n",
        ]
    )

    return header + body


def main() -> int:
    DOCS_OUT.mkdir(parents=True, exist_ok=True)
    id_map = _load_script_id_map()

    updated = 0
    for suite_dir in [SCRIPTS_DIR / "sanity", SCRIPTS_DIR / "stability"]:
        suite = suite_dir.name
        out_dir = DOCS_OUT / suite
        out_dir.mkdir(parents=True, exist_ok=True)

        for zp in sorted(suite_dir.glob("*.zip")):
            name = zp.stem
            manifest = _read_manifest(zp)
            sid = id_map.get((suite, name))
            page = _make_page(suite, name, sid, manifest)
            out_path = out_dir / f"{name}.md"
            out_path.write_text(page, encoding="utf-8")
            updated += 1

    print(f"[OK] generated/updated pages: {updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
