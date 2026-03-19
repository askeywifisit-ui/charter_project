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

echo "[5/8] Install cpe-metrics-agent env"
if test -f "$WORK/cpe-metrics-agent"; then
  sudo cp -a "$WORK/cpe-metrics-agent" /etc/default/cpe-metrics-agent
fi

echo "[6/8] Postgres (A: clean DB)"
sudo systemctl enable --now postgresql
sudo -iu postgres psql -c "CREATE USER rg WITH PASSWORD 'rg';" || true
sudo -iu postgres psql -c "CREATE DATABASE rg OWNER rg;" || true
sudo -iu postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE rg TO rg;" || true

echo "[7/8] Reload + start services"
sudo systemctl daemon-reload
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
