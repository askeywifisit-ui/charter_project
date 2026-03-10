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
    # Known cleartext values that must never ship in docs/artifacts
    ("Xin@Plume", "<fill>"),
    ("c-xin.guo@charter.com", "<fill>"),
    ("4p@ssThats10ng", "<fill>"),
    ("QA_Auto_Password_1234", "<fill>"),
]

# Scrub keyed values in manifest.yaml even if we don't know the exact literal.
PASSWORD_KEYS = [
    "SSH_PASSWORD",
    "SSH_PASSWORD_DEFAULT",
    "SSH_ENABLE_PASSWORD",
    "CPE_PASSWORD",
    "WAREHOUSE_PASSWORD",
    "NOC_PASSWORD",
]

EMAIL_KEYS = [
    "NOC_EMAIL",
]

PASSWORD_VALUE_RE = re.compile(
    r"^([ \t]*)(%s)([ \t]*:[ \t]*)(['\"]?)([^'\"#\n]*)(\4)([ \t]*(#.*)?)$"
    % "|".join(re.escape(k) for k in PASSWORD_KEYS),
    re.MULTILINE,
)

EMAIL_VALUE_RE = re.compile(
    r"^([ \t]*)(%s)([ \t]*:[ \t]*)(['\"]?)([^'\"#\n]*)(\4)([ \t]*(#.*)?)$"
    % "|".join(re.escape(k) for k in EMAIL_KEYS),
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

    # Keyed email scrubbing (e.g., NOC_EMAIL: someone@domain)
    def _sub_email(m: re.Match) -> str:
        indent, key, sep, quote, val, _, tail, _comment = m.groups()
        v = val.strip()
        if v in ("", "null", "<fill>"):
            return m.group(0)
        return f"{indent}{key}{sep}{quote}<fill>{quote}{tail}"

    text = EMAIL_VALUE_RE.sub(_sub_email, text)

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
