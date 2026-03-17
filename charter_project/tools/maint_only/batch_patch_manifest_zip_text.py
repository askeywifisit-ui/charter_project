#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
batch_patch_manifest_zip_text.py

Patch manifest.yaml inside zip(s) by TEXT-editing the `env:` block only,
so comments/blank lines/formatting are preserved.

Default behavior (quiet):
- NO per-file prints during processing (prevents screen spam)
- Print only summary/reports at the end

Use --verbose to print per-file [SKIP]/[CHANGED] lines.

Other features:
- Preserves comments/blank lines/formatting (no YAML re-dump)
- CHANGED lines shown in yellow (TTY only)
- Human-friendly summary + key impact report
- Hides 0-impact keys by default (avoids "500 lines" eye strain)
- Limits Changed/Skipped file lists by default
- IMPORTANT: preserves original zip's owner/group/mode/mtime to avoid PermissionError
  when you run this script as root (prevents root:root 600 issue).
- Output order at end: Summary -> Key Impact -> Failed -> Skipped -> (CHANGED FILES LAST)
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import shutil
import sys
import tempfile
import zipfile
from typing import Dict, List, Optional, Tuple

ENV_LINE_RE = re.compile(r"^(\s*)env:\s*(#.*)?$")
ENV_KV_RE = re.compile(r"^(\s*)([-A-Za-z0-9_]+)(\s*:\s*)(.*?)(\s*(#.*))?$")
SAFE_PLAIN_RE = re.compile(r"^[A-Za-z0-9_./:\-]+$")


# ---------- color helpers ----------
def _use_color(args: argparse.Namespace) -> bool:
    if getattr(args, "no_color", False):
        return False
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


def _yellow(args: argparse.Namespace, s: str) -> str:
    if not _use_color(args):
        return s
    return "\033[33m" + s + "\033[0m"


# ---------- yaml scalar token helpers (for compare/format preservation) ----------
def _unescape_single_quoted(s: str) -> str:
    return s.replace("''", "'")


def _unescape_double_quoted(s: str) -> str:
    # minimal unescape for compare usage
    s = s.replace('\\"', '"')
    s = s.replace("\\\\", "\\")
    return s


def _token_to_scalar_str(token: str) -> str:
    t = token.strip()
    if len(t) >= 2 and t[0] == "'" and t[-1] == "'":
        return _unescape_single_quoted(t[1:-1])
    if len(t) >= 2 and t[0] == '"' and t[-1] == '"':
        return _unescape_double_quoted(t[1:-1])
    return t


def _escape_single_quoted(v: str) -> str:
    return v.replace("'", "''")


def _escape_double_quoted(v: str) -> str:
    return v.replace("\\", "\\\\").replace('"', '\\"')


def _quote_single(v: str) -> str:
    return "'" + _escape_single_quoted(v) + "'"


def _quote_double(v: str) -> str:
    return '"' + _escape_double_quoted(v) + '"'


def _format_like_original(new_val: str, old_val_token: str) -> str:
    """
    Preserve original quoting style if present.
    If old was plain scalar, keep plain if safe; else single-quote.
    """
    s = old_val_token.strip()

    if len(s) >= 2 and s[0] == "'" and s[-1] == "'":
        return _quote_single(new_val)
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return _quote_double(new_val)

    if SAFE_PLAIN_RE.match(new_val):
        return new_val
    return _quote_single(new_val)


def _default_format_for_insert(v: str) -> str:
    # For inserted keys, keep it safe
    if SAFE_PLAIN_RE.match(v):
        return v
    return _quote_single(v)


# ---------- core patcher ----------
def patch_manifest_text(manifest_text: str, kv: Dict[str, str]) -> Tuple[str, List[str], List[str], List[str]]:
    """
    Returns: (new_text, updated_keys, added_keys, unchanged_keys)
    Only edits the env: block; preserves everything else including comments.
    """
    if not kv:
        return manifest_text, [], [], []

    lines = manifest_text.splitlines(True)  # keep line endings
    env_idx = None
    env_indent = ""

    for i, line in enumerate(lines):
        m = ENV_LINE_RE.match(line)
        if m:
            env_idx = i
            env_indent = m.group(1) or ""
            break

    if env_idx is None:
        # Append env: at end (minimal)
        if lines and not lines[-1].endswith("\n"):
            lines[-1] = lines[-1] + "\n"
        if not lines:
            lines = []
        lines.append("env:\n")
        env_idx = len(lines) - 1
        env_indent = ""

    def indent_len(s: str) -> int:
        return len(s) - len(s.lstrip(" "))

    base_indent_len = indent_len(env_indent)

    # Find env block end: first non-empty/non-comment line with indent <= env indent
    block_start = env_idx + 1
    block_end = len(lines)
    for j in range(block_start, len(lines)):
        raw = lines[j]
        stripped = raw.strip()
        if stripped == "" or stripped.startswith("#"):
            continue
        if indent_len(raw) <= base_indent_len:
            block_end = j
            break

    first_key_indent: Optional[str] = None
    key_to_line_index: Dict[str, int] = {}

    for j in range(block_start, block_end):
        m = ENV_KV_RE.match(lines[j])
        if not m:
            continue
        key_indent, key = m.group(1), m.group(2)
        if first_key_indent is None:
            first_key_indent = key_indent
        key_to_line_index[key] = j

    if first_key_indent is None:
        first_key_indent = env_indent + "  "

    updated: List[str] = []
    added: List[str] = []
    unchanged: List[str] = []

    # Update existing keys only if semantic value differs
    for k, v in kv.items():
        if k not in key_to_line_index:
            continue

        idx = key_to_line_index[k]
        m = ENV_KV_RE.match(lines[idx])
        if not m:
            continue

        key_indent, key, sep, old_val, comment = (
            m.group(1),
            m.group(2),
            m.group(3),
            (m.group(4) or ""),
            (m.group(6) or ""),
        )

        old_scalar = _token_to_scalar_str(old_val)
        if old_scalar == v:
            unchanged.append(k)
            continue

        new_token = _format_like_original(v, old_val)
        new_line = f"{key_indent}{key}{sep}{new_token}{comment}\n"
        lines[idx] = new_line
        updated.append(k)

    # Insert missing keys at end of env block
    missing = [k for k in kv.keys() if k not in key_to_line_index]
    if missing:
        insert_at = block_end
        for k in missing:
            v = kv[k]
            new_line = f"{first_key_indent}{k}: {_default_format_for_insert(v)}\n"
            lines.insert(insert_at, new_line)
            insert_at += 1
            added.append(k)

    return "".join(lines), updated, added, unchanged


def find_manifest_member(z: zipfile.ZipFile) -> Optional[str]:
    names = z.namelist()
    if "manifest.yaml" in names:
        return "manifest.yaml"
    cands = [n for n in names if n.endswith("/manifest.yaml") or n.endswith("\\manifest.yaml")]
    return cands[0] if cands else None


def _restore_file_metadata(path: str, uid: int, gid: int, mode: int, mtime: float, atime: float) -> None:
    """
    Restore owner/group/mode/timestamps.
    - chmod usually works if you own the file
    - chown works only as root; ignore PermissionError
    """
    try:
        os.chmod(path, mode)
    except PermissionError:
        pass

    try:
        os.chown(path, uid, gid)
    except PermissionError:
        pass

    try:
        os.utime(path, (atime, mtime))
    except PermissionError:
        pass


def patch_zip(zip_path: str, backup_dir: str, kv: Dict[str, str]) -> Dict[str, object]:
    # Capture original metadata to avoid root:root 600 issue after overwrite
    st = os.stat(zip_path)
    orig_uid, orig_gid = st.st_uid, st.st_gid
    orig_mode = st.st_mode & 0o777
    orig_mtime = st.st_mtime
    orig_atime = st.st_atime

    os.makedirs(backup_dir, exist_ok=True)
    backup_path = os.path.join(backup_dir, os.path.basename(zip_path))

    shutil.copy2(zip_path, backup_path)
    _restore_file_metadata(backup_path, orig_uid, orig_gid, orig_mode, orig_mtime, orig_atime)

    with zipfile.ZipFile(zip_path, "r") as zr:
        manifest_member = find_manifest_member(zr)
        if not manifest_member:
            return {"zip": zip_path, "ok": False, "error": "manifest.yaml not found"}

        raw = zr.read(manifest_member)
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("utf-8-sig")

        new_text, updated, added, unchanged = patch_manifest_text(text, kv)

        if not updated and not added:
            return {
                "zip": zip_path,
                "ok": True,
                "status": "SKIP",
                "updated": [],
                "added": [],
                "unchanged": unchanged,
                "backup": backup_path,
            }

        fd, tmp_path = tempfile.mkstemp(prefix="patch_", suffix=".zip")
        os.close(fd)

        try:
            with zipfile.ZipFile(tmp_path, "w") as zw:
                for info in zr.infolist():
                    data = zr.read(info.filename)
                    if info.filename == manifest_member:
                        data = new_text.encode("utf-8")

                    zi = zipfile.ZipInfo(info.filename)
                    zi.date_time = info.date_time
                    zi.compress_type = info.compress_type
                    zi.external_attr = info.external_attr
                    zi.internal_attr = info.internal_attr
                    zi.flag_bits = info.flag_bits
                    zw.writestr(zi, data, compress_type=info.compress_type)

            shutil.move(tmp_path, zip_path)

            # Restore original owner/mode/timestamps (critical fix)
            _restore_file_metadata(zip_path, orig_uid, orig_gid, orig_mode, orig_mtime, orig_atime)

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    return {
        "zip": zip_path,
        "ok": True,
        "status": "CHANGED",
        "updated": updated,
        "added": added,
        "unchanged": unchanged,
        "backup": backup_path,
    }


def parse_sets(sets: List[str]) -> Dict[str, str]:
    kv: Dict[str, str] = {}
    for item in sets:
        if "=" not in item:
            raise ValueError(f"--set expects KEY=VALUE, got: {item}")
        k, v = item.split("=", 1)
        k = k.strip()
        v = v.strip()
        if not k:
            raise ValueError(f"empty KEY in --set: {item}")
        kv[k] = v
    return kv


def _short(path: str) -> str:
    return os.path.basename(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", required=True, help="glob pattern to match zip files")
    ap.add_argument("--backup-dir", required=True, help="directory to store backups")
    ap.add_argument("--set", dest="sets", action="append", default=[], help="KEY=VALUE (repeatable)")

    # report controls (for "500 keys / 500 scripts" readability)
    ap.add_argument("--show-zero-keys", action="store_true",
                    help="also list 0-impact keys (default: hidden)")
    ap.add_argument("--zero-limit", type=int, default=30,
                    help="when --show-zero-keys, max 0-impact keys to print (default: 30)")
    ap.add_argument("--impact-limit", type=int, default=50,
                    help="max impacted keys to print (default: 50)")
    ap.add_argument("--changed-limit", type=int, default=60,
                    help="max changed files to print (default: 60)")
    ap.add_argument("--skipped-limit", type=int, default=60,
                    help="max skipped files to print (default: 60)")
    ap.add_argument("--no-color", action="store_true",
                    help="disable ANSI colors even on TTY")

    # NEW: suppress per-file prints by default
    ap.add_argument("--verbose", action="store_true",
                    help="print per-file [SKIP]/[CHANGED] lines during processing")

    args = ap.parse_args()
    kv = parse_sets(args.sets)

    paths = sorted(glob.glob(args.glob))
    if not paths:
        print(f"[ERR] no files matched: {args.glob}", file=sys.stderr)
        return 2

    # (Optional) You can comment this plan out if you want even quieter output
    print("=== Patch Plan (env values to enforce) ===")
    for k in sorted(kv.keys()):
        print(f"  - {k} = {kv[k]}")
    print("")

    results: List[Dict[str, object]] = []
    fail_cnt = 0

    for p in paths:
        try:
            r = patch_zip(p, args.backup_dir, kv)
        except Exception as e:
            fail_cnt += 1
            results.append({"zip": p, "ok": False, "error": repr(e)})
            if args.verbose:
                print(f"[FAIL] {_short(p)} :: {e!r}", file=sys.stderr)
            continue

        results.append(r)

        if not r.get("ok"):
            fail_cnt += 1
            if args.verbose:
                print(f"[FAIL] {_short(p)} :: {r.get('error')}", file=sys.stderr)
            continue

        # per-file prints ONLY in --verbose mode
        if args.verbose:
            if r.get("status") == "SKIP":
                print(f"[SKIP] {_short(p)} (already matches)")
            else:
                upd = r.get("updated", [])
                add = r.get("added", [])
                parts = []
                if upd:
                    parts.append(f"updated={upd}")
                if add:
                    parts.append(f"added={add}")
                print(_yellow(args, f"[CHANGED] {_short(p)} " + (" ".join(parts) if parts else "")))

    changed = [r for r in results if r.get("ok") and r.get("status") == "CHANGED"]
    skipped = [r for r in results if r.get("ok") and r.get("status") == "SKIP"]
    failed = [r for r in results if not r.get("ok")]

    # Key impact (count only on CHANGED zips)
    key_upd_cnt: Dict[str, int] = {k: 0 for k in kv.keys()}
    key_add_cnt: Dict[str, int] = {k: 0 for k in kv.keys()}

    for r in changed:
        for k in r.get("updated", []):
            key_upd_cnt[k] = key_upd_cnt.get(k, 0) + 1
        for k in r.get("added", []):
            key_add_cnt[k] = key_add_cnt.get(k, 0) + 1

    print("\n=== Summary ===")
    print(f"  total matched : {len(paths)}")
    print(f"  changed       : {len(changed)}")
    print(f"  skipped       : {len(skipped)}")
    print(f"  failed        : {len(failed)}")
    print(f"  backup_dir    : {args.backup_dir}")

    print("\n=== Key Impact (how many scripts were affected) ===")
    items = []
    for k in kv.keys():
        u = key_upd_cnt.get(k, 0)
        a = key_add_cnt.get(k, 0)
        t = u + a
        items.append((t, k, u, a))

    impacted = [it for it in items if it[0] > 0]
    zeros = [it for it in items if it[0] == 0]

    impacted.sort(key=lambda x: (-x[0], x[1]))
    zeros.sort(key=lambda x: x[1])

    if impacted:
        shown = impacted[: args.impact_limit]
        for t, k, u, a in shown:
            extra = []
            if u:
                extra.append(f"update {u}")
            if a:
                extra.append(f"add {a}")
            print(f"  - {k}: {t} ({', '.join(extra)})")

        if len(impacted) > args.impact_limit:
            print(f"  ... ({len(impacted) - args.impact_limit} more impacted keys hidden; "
                  f"use --impact-limit N to show more)")
    else:
        print("  (no keys impacted)")

    if zeros:
        print("  ---")
        print(f"  0-impact keys: {len(zeros)} hidden (use --show-zero-keys to list)")
        if args.show_zero_keys:
            zshown = zeros[: args.zero_limit]
            for _, k, _, _ in zshown:
                print(f"  - {k}: 0 (no script needed change)")
            if len(zeros) > args.zero_limit:
                print(f"  ... ({len(zeros) - args.zero_limit} more 0-impact keys hidden; "
                      f"use --zero-limit N to show more)")

    # Lists at end: Failed -> Skipped -> Changed (CHANGED LAST)
    if failed:
        print("\n=== Failed Files ===")
        for r in failed:
            print(f"  - {_short(str(r.get('zip')))} :: {r.get('error')}")

    if skipped:
        print("\n=== Skipped Files (already correct) ===")
        shown = skipped[: args.skipped_limit]
        for r in shown:
            print(f"  - {_short(str(r.get('zip')))}")
        if len(skipped) > args.skipped_limit:
            print(f"  ... ({len(skipped) - args.skipped_limit} more skipped files hidden; "
                  f"use --skipped-limit N to show more)")

    # ✅ Put changed files at the very end
    if changed:
        print("\n=== Changed Files ===")
        shown = changed[: args.changed_limit]
        for r in shown:
            zp = _short(str(r.get("zip")))
            upd = r.get("updated", [])
            add = r.get("added", [])
            msg = []
            if upd:
                msg.append(f"updated={upd}")
            if add:
                msg.append(f"added={add}")
            print(_yellow(args, f"  - {zp} " + (" ".join(msg) if msg else "")))
        if len(changed) > args.changed_limit:
            print(f"  ... ({len(changed) - args.changed_limit} more changed files hidden; "
                  f"use --changed-limit N to show more)")

    return 0 if fail_cnt == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

