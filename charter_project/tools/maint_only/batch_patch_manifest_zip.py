#!/usr/bin/env python3
"""
batch_patch_manifest_zip.py

目標（更人性化）
- 批次修改 zip 內的 manifest.yaml（不需要解整包）
- --set 支援兩種寫法：
    A) bare key：        --set CYCLES=10
       若 manifest 有 env: dict -> 自動改 env.CYCLES（且會自動轉字串 "10"）
       若沒有 env: dict -> 改 top-level CYCLES
    B) dotted key：      --set env.CYCLES=10 / --set wifi.TEST_PSK="12345678"
       依你指定的路徑修改（其中 env.* 仍會自動轉字串）

- 若你要強制改 top-level（即使有 env）：
    --set .CYCLES=10
    --set root.CYCLES=10

- deep merge：--merge "{env: {SSH_USER: operator}}"

權限/owner（避免 worker PermissionError）
- 預設會對每個 zip 套用：
    chmod 644
    若用 root 跑：chown 成「zip 所在資料夾」的 owner/group（通常是 da40:da40）
- 可用 --no-fix-perms 關掉
- 可用 --fix-owner / --fix-mode 覆蓋 auto 行為
"""

import argparse
import copy
import glob
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

import yaml


# -----------------------------
# YAML / dict helpers
# -----------------------------
def deep_merge(dst, src):
    """遞迴合併 dict；非 dict 類型直接覆蓋。"""
    if not isinstance(dst, dict) or not isinstance(src, dict):
        return src
    for k, v in src.items():
        if k in dst and isinstance(dst[k], dict) and isinstance(v, dict):
            deep_merge(dst[k], v)
        else:
            dst[k] = v
    return dst


def set_path(d, dotted_key, value):
    """支援 dotted key： set_path({}, "env.CYCLES", "10") -> {"env":{"CYCLES":"10"}}"""
    keys = dotted_key.split(".")
    cur = d
    for k in keys[:-1]:
        if k not in cur or not isinstance(cur[k], dict):
            cur[k] = {}
        cur = cur[k]
    cur[keys[-1]] = value


def parse_value_as_yaml(s: str):
    """
    讓 CLI value 用 YAML 表達型別：
      10 -> int
      true -> bool
      "10" 或 '10' -> str
    """
    return yaml.safe_load(s)


# -----------------------------
# zip helpers
# -----------------------------
def find_manifest_path(zf: zipfile.ZipFile):
    """在 zip 裡找 manifest.yaml，挑路徑最短者（通常在根目錄）。"""
    cand = [n for n in zf.namelist() if n.endswith("manifest.yaml")]
    if not cand:
        cand = [n for n in zf.namelist() if n.lower().endswith("manifest.yaml")]
    if not cand:
        return None
    return sorted(cand, key=lambda x: (x.count("/"), len(x)))[0]


def rewrite_zip_replace_file_preserve_stat(zip_path: Path, target_name: str, new_bytes: bytes):
    """
    用「重建新 zip」方式替換某個檔案內容，再 replace 掉舊 zip。
    會先保留原本 zip 的 stat（owner/mode/time），replace 後還原。
    注意：若原本 zip 權限本來就壞（root:root 600），後面還會再套用 fix-perms 進一步修正。
    """
    st = zip_path.stat()

    tmp_fd, tmp_name = tempfile.mkstemp(suffix=".zip", prefix=zip_path.name + ".tmp.")
    os.close(tmp_fd)
    tmp_path = Path(tmp_name)

    with zipfile.ZipFile(zip_path, "r") as zin, zipfile.ZipFile(tmp_path, "w") as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename == target_name:
                data = new_bytes
            zout.writestr(info, data)

    tmp_path.replace(zip_path)

    os.chmod(zip_path, st.st_mode)
    try:
        os.chown(zip_path, st.st_uid, st.st_gid)
    except PermissionError:
        pass
    os.utime(zip_path, (st.st_atime, st.st_mtime))


# -----------------------------
# perms helpers
# -----------------------------
def parse_owner(owner: str):
    """解析 'user:group' -> (uid, gid)"""
    import pwd
    import grp

    if ":" not in owner:
        raise ValueError('owner format must be "user:group", e.g. da40:da40')
    user, group = owner.split(":", 1)
    uid = pwd.getpwnam(user).pw_uid
    gid = grp.getgrnam(group).gr_gid
    return uid, gid


def parse_mode(mode_str: str):
    """解析 644 / 0644 / 0o644 -> int"""
    s = str(mode_str).strip().lower()
    if s.startswith("0o"):
        return int(s, 8)
    if s.startswith("0") and s != "0":
        return int(s, 8)
    return int(s, 8)


def fix_perms_auto(zip_path: Path, *, force_owner: str | None, force_mode: str | None):
    """
    預設修正策略（人性化）：
    - mode：預設 644（或使用 force_mode）
    - owner/group：
        - 若 force_owner 有指定：照指定
        - 否則若 euid==0（root）：自動 chown 成 zip 所在資料夾的 owner/group
        - 非 root：不 chown（避免 PermissionError）
    """
    # 1) chmod
    mode = parse_mode(force_mode) if force_mode else 0o644
    os.chmod(zip_path, mode)

    # 2) chown
    if os.geteuid() != 0:
        return

    if force_owner:
        uid, gid = parse_owner(force_owner)
    else:
        pst = zip_path.parent.stat()
        uid, gid = pst.st_uid, pst.st_gid

    try:
        os.chown(zip_path, uid, gid)
    except PermissionError:
        pass


# -----------------------------
# key normalization (human-friendly)
# -----------------------------
def normalize_set_key(raw_key: str, manifest: dict) -> tuple[str, bool]:
    """
    回傳 (final_key, is_env_leaf)
    規則：
    - root.X 或 .X 強制 top-level
    - 已經 dotted 的照用
    - bare KEY：若 manifest 有 env dict -> env.KEY；否則 top-level KEY
    """
    k = raw_key.strip()

    if k.startswith("root."):
        return k[len("root.") :], False
    if k.startswith("."):
        return k[1:], False

    if "." in k:
        # dotted path，若是 env.xxx 視為 env leaf（用來自動轉字串）
        return k, (k.startswith("env.") and len(k) > 4)

    has_env = isinstance(manifest.get("env"), dict)
    if has_env:
        return f"env.{k}", True
    return k, False


def stringify_if_env_leaf(key: str, value):
    """寫入 env.* 時，統一轉成字串（env 本質是字串）。"""
    if key.startswith("env.") and len(key) > 4 and not isinstance(value, str):
        return str(value)
    return value


# -----------------------------
# main
# -----------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", required=True, help='zip glob，例如 "/home/.../upload_*.zip"')
    ap.add_argument("--backup-dir", default="", help="備份目錄（建議開）")
    ap.add_argument("--dry-run", action="store_true", help="只顯示會改哪些 zip，不寫回")
    ap.add_argument("--set", action="append", default=[], help='設定 KEY=VALUE（可多次）；支援 dotted key')
    ap.add_argument("--merge", action="append", default=[], help='深度合併 YAML dict，例如 "{env:{CYCLES:\'10\'}}"')

    # 預設會修 perms，避免 worker 讀不到
    ap.add_argument("--no-fix-perms", action="store_true", help="不自動修正 zip 權限/owner")
    ap.add_argument("--fix-owner", default="", help='指定 owner，例如 "da40:da40"（會覆蓋 auto owner）')
    ap.add_argument("--fix-mode", default="", help="指定 mode，例如 644（會覆蓋預設 644）")

    args = ap.parse_args()

    zips = sorted(glob.glob(args.glob))
    if not zips:
        raise SystemExit(f"no zip matched: {args.glob}")

    backup_dir = Path(args.backup_dir).expanduser() if args.backup_dir else None
    if backup_dir:
        backup_dir.mkdir(parents=True, exist_ok=True)

    force_owner = args.fix_owner.strip() or None
    force_mode = args.fix_mode.strip() or None

    for zp in map(Path, zips):
        # 讀 manifest.yaml
        with zipfile.ZipFile(zp, "r") as zf:
            mpath = find_manifest_path(zf)
            if not mpath:
                print(f"[SKIP] {zp.name}: manifest.yaml not found")
                if not args.no_fix_perms and not args.dry_run:
                    fix_perms_auto(zp, force_owner=force_owner, force_mode=force_mode)
                continue

            raw = zf.read(mpath).decode("utf-8", errors="replace")
            manifest = yaml.safe_load(raw) or {}
            if not isinstance(manifest, dict):
                print(f"[SKIP] {zp.name}: manifest.yaml is not a dict")
                if not args.no_fix_perms and not args.dry_run:
                    fix_perms_auto(zp, force_owner=force_owner, force_mode=force_mode)
                continue

        patch = {}

        # --set KEY=VALUE（人性化：bare key -> env.KEY）
        for item in args.set:
            if "=" not in item:
                raise SystemExit(f"bad --set: {item} (need KEY=VALUE)")
            raw_k, raw_v = item.split("=", 1)

            final_k, _is_env_leaf = normalize_set_key(raw_k, manifest)
            v = parse_value_as_yaml(raw_v.strip())
            v = stringify_if_env_leaf(final_k, v)

            set_path(patch, final_k, v)

        # --merge "<yaml dict>"
        for m in args.merge:
            md = yaml.safe_load(m)
            if not isinstance(md, dict):
                raise SystemExit(f"bad --merge (must be YAML dict): {m}")
            deep_merge(patch, md)

        new_manifest = copy.deepcopy(manifest)
        deep_merge(new_manifest, patch)

        before = yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True)
        after = yaml.safe_dump(new_manifest, sort_keys=False, allow_unicode=True)

        changed = (before != after)
        if changed:
            print(f"[PATCH] {zp.name} -> {mpath}")
            if args.dry_run:
                continue

            if backup_dir:
                shutil.copy2(zp, backup_dir / zp.name)

            rewrite_zip_replace_file_preserve_stat(zp, mpath, after.encode("utf-8"))
        else:
            print(f"[NOOP]  {zp.name}: no manifest change")

        # 每包 zip 結束後都修 perms（預設開啟）
        if not args.no_fix_perms and not args.dry_run:
            fix_perms_auto(zp, force_owner=force_owner, force_mode=force_mode)

    print("done.")


if __name__ == "__main__":
    main()

