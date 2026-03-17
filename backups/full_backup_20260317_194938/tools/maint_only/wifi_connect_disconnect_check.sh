#!/usr/bin/env bash
set -euo pipefail

# Wi-Fi connect -> status -> disconnect -> status using wifi_iwd.py.
#
# Non-root mode:
# - Requires passwordless sudo (-n) for running wifi_iwd.py as root
# - Recommended sudoers:
#     Defaults:<user> env_keep += "WIFI_PSK"
#     <user> ALL=(root) NOPASSWD: /usr/bin/python3 /home/da40/charter/tools/wifi_iwd.py *
#
# Usage:
#   export WIFI_PSK='...'
#   ./wifi_connect_disconnect_check_v2.sh

WIFI_TOOL="${WIFI_TOOL:-/home/da40/charter/tools/wifi_iwd.py}"
WIFI_IFACE="${WIFI_IFACE:-wlx6cb0ce1ff230}"
WIFI_SSID="${WIFI_SSID:-SpectrumSetup-6A4D}"
WIFI_BAND="${WIFI_BAND:-5g}"              # 2g|5g|6g
WIFI_PSK="${WIFI_PSK:-}"

if [[ -z "${WIFI_PSK}" ]]; then
  echo "[ERR] WIFI_PSK is empty. Please: export WIFI_PSK='...'"
  exit 2
fi

# Ensure WIFI_PSK is exported so sudo env_keep can preserve it
export WIFI_PSK

SUDO=()
if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  SUDO=(sudo -n)
fi

run() {
  echo
  echo ">> ${SUDO[*]} $*"
  "${SUDO[@]}" "$@"
}

echo "[INFO] iface=${WIFI_IFACE} ssid=${WIFI_SSID} band=${WIFI_BAND}"
echo "[INFO] tool=${WIFI_TOOL} euid=$(id -u) sudo_mode=$([[ ${#SUDO[@]} -gt 0 ]] && echo yes || echo no)"

run /usr/bin/python3 "${WIFI_TOOL}" --json disconnect   --iface "${WIFI_IFACE}"   --restore-nm --unmanaged

# 1) connect (ensure)
run /usr/bin/python3 "${WIFI_TOOL}" --json ensure   --iface "${WIFI_IFACE}"   --ssid "${WIFI_SSID}"   --band "${WIFI_BAND}"   --password-env WIFI_PSK   --takeover --restore-nm --unmanaged

# 2) status
run /usr/bin/python3 "${WIFI_TOOL}" --json status --iface "${WIFI_IFACE}"

# 3) disconnect
#run /usr/bin/python3 "${WIFI_TOOL}" --json disconnect   --iface "${WIFI_IFACE}"   --restore-nm --unmanaged

# 4) status again
#run /usr/bin/python3 "${WIFI_TOOL}" --json status --iface "${WIFI_IFACE}"

echo
echo "[OK] Done."

