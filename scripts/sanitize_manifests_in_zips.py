#!/usr/bin/env python3
"""Sanitize sensitive values inside script zip manifests.

- Replaces known cleartext credentials/password examples with placeholders.
- Only touches manifest.yaml inside *.zip.

Usage:
  python3 scripts/sanitize_manifests_in_zips.py
"""

from __future__ import annotations

import glob
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

REPLACEMENTS = [
    ("<fill>", "<fill>"),
    ("<fill>", "<fill>"),
    ("<fill>", "<fill>"),
    ("<fill>", "<fill>"),
]

# For generic examples like <fill>, only sanitize when it appears as a password value.
PASSWORD_KEYS = [
    "SSH_PASSWORD",
    "SSH_PASSWORD_DEFAULT",
    "SSH_ENABLE_PASSWORD",
    "CPE_PASSWORD",
    "WAREHOUSE_PASSWORD",
    "NOC_PASSWORD",
]

PASSWORD_VALUE_RE = re.compile(
    r"^([ \t]*)(%s)([ \t]*:[ \t]*)(['\"]?)([^'\"#\n]*)(\4)([ \t]*(#.*)?)$"
    % "|".join(re.escape(k) for k in PASSWORD_KEYS),
    re.MULTILINE,
)


def sanitize_manifest(text: str) -> tuple[str, bool]:
    orig = text

    # Direct known string replacements
    for a, b in REPLACEMENTS:
        text = text.replace(a, b)

    # Keyed password value scrubbing (e.g., SSH_PASSWORD: '<fill>')
    def _sub(m: re.Match) -> str:
        indent, key, sep, quote, val, _, tail, _comment = m.groups()
        # Keep null/<fill>/empty as-is
        v = val.strip()
        if v in ("", "null", "<fill>"):
            return m.group(0)
        return f"{indent}{key}{sep}{quote}<fill>{quote}{tail}"

    text = PASSWORD_VALUE_RE.sub(_sub, text)

    return text, (text != orig)


def main() -> int:
    zips = sorted(glob.glob("scripts/**/*.zip", recursive=True))
    changed = 0
    touched = 0

    for zp in zips:
        with zipfile.ZipFile(zp, "r") as z:
            if "manifest.yaml" not in z.namelist():
                continue
            raw = z.read("manifest.yaml")

        text = raw.decode("utf-8", "ignore")
        new_text, did = sanitize_manifest(text)
        if not did:
            continue

        touched += 1
        # Rewrite zip: copy all entries, replace manifest.yaml
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".zip")
        os.close(tmp_fd)
        try:
            with zipfile.ZipFile(zp, "r") as zin, zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as zout:
                for info in zin.infolist():
                    data = zin.read(info.filename)
                    if info.filename == "manifest.yaml":
                        data = new_text.encode("utf-8")
                    zout.writestr(info, data)
            shutil.move(tmp_path, zp)
            changed += 1
            print(f"[OK] sanitized: {zp}")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    print(f"\nTouched zips: {touched}; Updated zips: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
