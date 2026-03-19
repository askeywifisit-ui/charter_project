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

if sudo test -d /etc/systemd/system/charter-api.service.d; then
  sudo cp -a /etc/systemd/system/charter-api.service.d "$OUTDIR/"
fi

echo "[4/7] Export /etc/default/cpe-metrics-agent"
if sudo test -f /etc/default/cpe-metrics-agent; then
  sudo cp -a /etc/default/cpe-metrics-agent "$OUTDIR/"
fi

echo "[5/7] Export DB (optional - commented by default)"
echo "[6/7] Secrets handling"
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
  echo "ACTION REQUIRED: customer must fill noc_profiles.json" > "$OUTDIR/secrets_template/README.txt"
fi

echo "[7/7] Pack + sha256"
( cd "$OUTDIR" && tar -czf "$PKG" . )
sha256sum "$PKG" > "${PKG}.sha256" || shasum -a 256 "$PKG" > "${PKG}.sha256"

echo "OK: $PKG"
