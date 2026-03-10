#!/usr/bin/env python3
"""Generate/refresh docs pages for each test case based on latest 11F_140 exported zips.

Inputs:
- scripts/sanity/*.zip and scripts/stability/*.zip (must contain manifest.yaml)
- 11F_140 API list: CHARTER_BASE (default http://172.14.1.140:5173) to map name->script id

Outputs:
- docs/charter_site/docs/test_suites/<suite>/<name>.md

Rules:
- Audience: internal colleagues. Make it "follow steps and run" friendly.
- DO NOT publish secrets. Any key that looks sensitive is rendered as <fill>.
- Keep format consistent across pages.
- Prefer short sections + collapsible full manifest.

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


def _purpose_from_name(name: str) -> str:
    # Heuristic short purpose line for colleagues.
    n = name.lower()
    if "ssh" in n:
        return "SSH 行為/權限驗證（allow/deny/port/session/credential 等）"
    if "upnp" in n:
        return "UPnP enable/disable 與狀態驗證"
    if "dhcp" in n and "reservation" in n:
        return "DHCP reservation CRUD/穩定性驗證"
    if "wifi" in n or "wlan" in n or "ssid" in n:
        return "Wi‑Fi/SSID 連線與 radio 行為驗證"
    if "speedtest" in n:
        return "速度測試/長跑穩定性驗證"
    if "reboot" in n:
        return "reboot/多次重啟壓力驗證"
    if "factory" in n:
        return "Factory Reset/回復出廠驗證"
    return "（依腳本實作為準）"


def _make_page(suite: str, name: str, script_id_140: int | None, manifest: dict) -> str:
    version = manifest.get("version", "")
    entrypoint = manifest.get("entrypoint", "")
    env = manifest.get("env") or {}
    if not isinstance(env, dict):
        env = {}

    # scrub env
    env_scrubbed: dict[str, object] = {}
    for k, v in env.items():
        env_scrubbed[str(k)] = _scrub_value(str(k), v)

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

    # Compose a minimal env subset for display, and keep full env collapsible
    env_subset = {k: env_scrubbed[k] for k in preferred if k in env_scrubbed}

    now = _dt.datetime.now().strftime("%Y-%m-%d")
    sid_line = f"`11F_140={script_id_140}`" if script_id_140 else "（尚未對應）"
    purpose = _purpose_from_name(name)

    header = f"# {name}\n\n- Suite: **{suite}**\n- Script ID（可能因 delete/import 變動）：{sid_line}\n- 版本（manifest version）：`{version}`\n- Entrypoint：`{entrypoint}`\n\n> 本頁由工具依 11F_140 最新 export zip 自動產生/更新（{now}）。\n"

    body = "\n".join(
        [
            "\n## 一句話說明\n",
            f"- {purpose}\n",
            "\n## 你需要準備什麼（Preconditions）\n",
            "- 平台服務正常：web/api/worker\n- tools 可用：`/home/da40/charter/tools`\n- secrets 不要寫死在 manifest（NOC/SSH/Warehouse 等一律用 `<fill>`/`.secrets`）\n",
            "\n## 你只要改哪些參數（Top env）\n",
            ("\n".join(key_env_lines) + "\n") if key_env_lines else "（此腳本沒有常見可調 env）\n",
            "\n## Run（API）\n",
            "```bash\nexport CHARTER_BASE=\"http://<CONTROL_PC_IP>:5173\"\nSCRIPT_ID=<SCRIPT_ID_11F_140>\n# 建議先確認 worker 正常\ncurl -fsSL \"$CHARTER_BASE/api/runs/worker/status\" | python3 -m json.tool\n# 送出 run\ncurl -sS -X POST \"$CHARTER_BASE/api/scripts/$SCRIPT_ID/run\" | python3 -m json.tool\n```\n",
            "\n## 怎麼看結果（Evidence）\n",
            "```bash\nRID=<RUN_ID>\ncurl -sS \"$CHARTER_BASE/api/runs/$RID/log\" > run_${RID}_log.json\n# 若 fail-hook 有產生 cpe logs\ncurl -sS \"$CHARTER_BASE/api/runs/$RID/log-archives\" | python3 -m json.tool\ncurl -fsSL \"$CHARTER_BASE/api/runs/$RID/log-archive\" -o run_${RID}_cpe_log.tar.gz\n```\n",
            "\n## Cleanup\n",
            "```bash\n# 清理已完成的 runs + workdir（避免磁碟累積）\ncurl -sS -X DELETE \"$CHARTER_BASE/api/runs/purge?older_than_days=0\" | python3 -m json.tool\n```\n",
            "\n??? note \"manifest.yaml（節錄：常用 env）\"\n",
            "    ```yaml\n" + textwrap.indent(_yaml_dump_block({"env": env_subset}), "    ") + "\n    ```\n",
            "\n??? note \"manifest.yaml（完整 env，已自動去敏）\"\n",
            "    ```yaml\n" + textwrap.indent(_yaml_dump_block({"name": name, "suite": suite, "version": version, "entrypoint": entrypoint, "env": env_scrubbed}), "    ") + "\n    ```\n",
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
