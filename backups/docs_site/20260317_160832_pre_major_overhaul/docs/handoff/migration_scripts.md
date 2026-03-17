# 移植腳本（Export / Import 一鍵範本）

本頁提供兩支「可直接貼去跑」的移植腳本範本：

- `charter_migration_export.sh`：在來源 controlpc 匯出 migration pack
- `charter_migration_import.sh`：在新機器匯入 migration pack

> 設計原則：能重建、可稽核、避免把 secrets 明文交付。

---

## 1) Export（在來源 controlpc）

> **標準交付帳號：`da40`（需具備 sudo）**。實務上：
> - 以 `da40` 維護 `/home/da40/charter` 目錄與檔案 owner
> - 需要 root 權限的步驟（apt/systemd、/etc/default）由 sudo 執行
> - 如客戶只給 root/其他帳號，請務必仍建立 `/home/da40/charter`（或同步改 unit 內路徑）

把下面存成：`/home/da40/charter/charter_migration_export.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

TS=$(date +%Y%m%d_%H%M%S)
OUTDIR=/home/da40/charter-migration-${TS}
PKG=${OUTDIR}/charter_migration_${TS}.tgz

mkdir -p "$OUTDIR"

echo "[1/7] Export apps/tools"
cp -a /home/da40/charter/apps/api  "$OUTDIR/apps_api"
cp -a /home/da40/charter/apps/web  "$OUTDIR/apps_web"
cp -a /home/da40/charter/tools     "$OUTDIR/tools"

echo "[2/7] Export helper scripts"
cp -a /home/da40/charter/restart.all.charter.sh "$OUTDIR/" || true
cp -a /home/da40/charter/log.color.charter.sh   "$OUTDIR/" || true

echo "[3/7] Export systemd units"
sudo cp -a /etc/systemd/system/charter-api.service            "$OUTDIR/" || true
sudo cp -a /etc/systemd/system/charter-worker.service          "$OUTDIR/" || true
sudo cp -a /etc/systemd/system/charter-web.service             "$OUTDIR/" || true
sudo cp -a /etc/systemd/system/cpe-metrics-agent.service       "$OUTDIR/" || true
sudo cp -a /etc/systemd/system/cpe-status-probe.service        "$OUTDIR/" || true
sudo cp -a /etc/systemd/system/cpe-status-probe.timer          "$OUTDIR/" || true
sudo cp -a /etc/systemd/system/pbr-watchdog.service            "$OUTDIR/" || true

# drop-in（若存在）
if sudo test -d /etc/systemd/system/charter-api.service.d; then
  sudo cp -a /etc/systemd/system/charter-api.service.d "$OUTDIR/"
fi

echo "[4/7] Export /etc/default/cpe-metrics-agent"
if sudo test -f /etc/default/cpe-metrics-agent; then
  sudo cp -a /etc/default/cpe-metrics-agent "$OUTDIR/"
fi

echo "[5/7] Export DB (optional)"
# 預設不 dump，交付版通常走 A 乾淨建 DB。
# 若你要保留 runs/history，再解除註解：
# sudo -iu postgres pg_dump -Fc rg > "$OUTDIR/rg.dump"

echo "[6/7] Secrets handling"
# 不建議直接交付 .secrets；改提供 template。
if test -f /home/da40/charter/.secrets/noc_profiles.json; then
  mkdir -p "$OUTDIR/secrets_template"
  cat > "$OUTDIR/secrets_template/noc_profiles.template.json" <<'JSON'
{
  "<YOUR_PROFILE_NAME>": {
    "base": "https://<your-noc-endpoint>",
    "email": "<your-email>",
    "password": "<your-password>"
  }
}
JSON

  echo "ACTION REQUIRED: customer must fill noc_profiles.json (do NOT ship real secrets)." > "$OUTDIR/secrets_template/README.txt"
fi

echo "[7/7] Pack + sha256"
( cd "$OUTDIR" && tar -czf "$PKG" . )
sha256sum "$PKG" > "${PKG}.sha256" || shasum -a 256 "$PKG" > "${PKG}.sha256"

echo "OK: $PKG"
```

執行：

```bash
chmod +x /home/da40/charter/charter_migration_export.sh
/home/da40/charter/charter_migration_export.sh
```

產出 `charter_migration_*.tgz` 後，用 `scp` 搬到新機器。

---

## 2) Import（在新機器 / 新 VM）

把下面存成：`/home/da40/charter_migration_import.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

PKG=${1:?"Usage: $0 charter_migration_XXXX.tgz"}
WORK=/home/da40/charter_migration_work

echo "[1/8] Prepare dirs"
mkdir -p "$WORK"
mkdir -p /home/da40/charter/apps /home/da40/charter/tools

echo "[2/8] Unpack"
tar -xzf "$PKG" -C "$WORK"

echo "[3/8] Place apps/tools"
rm -rf /home/da40/charter/apps/api /home/da40/charter/apps/web /home/da40/charter/tools
mv "$WORK/apps_api" /home/da40/charter/apps/api
mv "$WORK/apps_web" /home/da40/charter/apps/web
mv "$WORK/tools"    /home/da40/charter/tools

echo "[4/8] Install systemd units"
sudo cp -a "$WORK"/*.service /etc/systemd/system/ 2>/dev/null || true
sudo cp -a "$WORK"/*.timer   /etc/systemd/system/ 2>/dev/null || true
if test -d "$WORK/charter-api.service.d"; then
  sudo mkdir -p /etc/systemd/system/charter-api.service.d
  sudo cp -a "$WORK/charter-api.service.d"/* /etc/systemd/system/charter-api.service.d/
fi

echo "[5/8] Install cpe-metrics-agent env (review before enable)"
if test -f "$WORK/cpe-metrics-agent"; then
  sudo cp -a "$WORK/cpe-metrics-agent" /etc/default/cpe-metrics-agent
fi

echo "[6/8] Postgres (A: clean DB)"
# A) 乾淨建 DB（交付推薦）
sudo systemctl enable --now postgresql
sudo -iu postgres psql -c "CREATE USER rg WITH PASSWORD 'rg';" || true
sudo -iu postgres psql -c "CREATE DATABASE rg OWNER rg;" || true
sudo -iu postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE rg TO rg;" || true

# B) 若有 rg.dump，且你要保留 runs/history：
# sudo -iu postgres pg_restore -d rg "$WORK/rg.dump"

echo "[7/8] Reload + start services"
sudo systemctl daemon-reload

# 建議啟動順序（同 controlpc）
sudo systemctl enable --now charter-api.service
sudo systemctl enable --now charter-worker.service
sudo systemctl enable --now cpe-metrics-agent.service
sudo systemctl enable --now cpe-status-probe.timer
sudo systemctl enable --now charter-web.service
sudo systemctl enable --now pbr-watchdog.service

echo "[8/8] Health check"
curl -sS http://127.0.0.1:5173/api/health || true
sudo systemctl status charter-api.service charter-worker.service charter-web.service --no-pager || true

echo "DONE"
```

執行：

```bash
chmod +x /home/da40/charter_migration_import.sh
/home/da40/charter_migration_import.sh /home/da40/charter_migration_XXXX.tgz
```

---

## 3) 交付前必做 checklist

- [ ] 確認 `DATABASE_URL`（systemd drop-in）在新機器仍正確。
- [ ] 檢查 `/etc/default/cpe-metrics-agent`：serial device/iface/password/interval。
- [ ] 確認 `.secrets/noc_profiles.json` 由對方填入（不要交付明文）。
- [ ] `systemctl status ...` 全綠。
- [ ] `curl http://<CONTROL_PC_IP>:5173/api/health` 回 `{"ok":true}`。
