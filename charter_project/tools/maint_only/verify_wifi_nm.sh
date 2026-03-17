#!/usr/bin/env bash
set -euo pipefail

# ---------------------------
# verify_wifi_nm.sh
# Validate wifi_nm.py "status" and "ensure" end-to-end.
#
# NOTE:
#   wifi_nm.py defines --json as a GLOBAL option, so it must appear BEFORE the subcommand:
#     python3 wifi_nm.py --json status ...
#     python3 wifi_nm.py --json ensure ...
# ---------------------------

TOOL="${TOOL:-/home/da40/charter/tools/wifi_nm.py}"
IFACE="${IFACE:-}"
SSID="${SSID:-}"
BSSID="${BSSID:-}"
CPE_IP="${CPE_IP:-192.168.1.1}"     # optional, adjust if your CPE LAN IP differs
PING_TARGET="${PING_TARGET:-}"      # optional, e.g. 8.8.8.8
BAND="${BAND:-5g}"                  # 5g|2g|any (used when BSSID not provided)
TIMEOUT="${TIMEOUT:-30}"
NEVER_DEFAULT="${NEVER_DEFAULT:-1}" # 1 to enable (wifi_nm.py default is already never-default unless --allow-default)
PASSWORD_ENV="${PASSWORD_ENV:-WIFI_PSK}" # prefer env var so PSK won't appear in argv

usage() {
  cat <<EOF
Usage:
  $0 --iface <ifname> --ssid <ssid> [--bssid <bssid>] [--tool <path>] [--cpe-ip <ip>] [--ping <ip>]

Env (optional):
  TOOL=/path/to/wifi_nm.py
  WIFI_PSK=your_password               (default password env var)
  PASSWORD_ENV=OTHER_ENV_NAME          (if you use a different env var name)
  BAND=5g|2g|any
  TIMEOUT=30
  NEVER_DEFAULT=1|0

Examples:
  export WIFI_PSK="12345678"
  $0 --iface wlx6cb0ce1ff230 --ssid "2F_RH-Test" --bssid 90:D3:CF:EB:6A:4B --cpe-ip 192.168.1.1
  $0 --iface wlx6cb0ce1ff230 --ssid "2F_RH-Test" --cpe-ip 192.168.1.1     # let tool auto-pick BSSID
EOF
}

log() { echo "[$(date '+%F %T')] $*"; }

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || { echo "ERROR: missing command: $1" >&2; exit 2; }
}

# ---- arg parse ----
while [[ $# -gt 0 ]]; do
  case "$1" in
    --tool) TOOL="$2"; shift 2 ;;
    --iface) IFACE="$2"; shift 2 ;;
    --ssid) SSID="$2"; shift 2 ;;
    --bssid) BSSID="$2"; shift 2 ;;
    --cpe-ip) CPE_IP="$2"; shift 2 ;;
    --ping) PING_TARGET="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 2 ;;
  esac
done

[[ -n "$IFACE" && -n "$SSID" ]] || { usage; exit 2; }

# ---- preflight ----
need_cmd python3
need_cmd nmcli
need_cmd iw
need_cmd ip

[[ -f "$TOOL" ]] || { echo "ERROR: wifi tool not found: $TOOL" >&2; exit 2; }

log "TOOL=$TOOL"
log "IFACE=$IFACE SSID=$SSID BSSID=${BSSID:-<auto>} BAND=$BAND TIMEOUT=$TIMEOUT"
log "CPE_IP=$CPE_IP PING_TARGET=${PING_TARGET:-<skip>}"
log "Password via env: ${PASSWORD_ENV} (set it if needed)."

if [[ -z "${!PASSWORD_ENV:-}" ]]; then
  log "WARN: env ${PASSWORD_ENV} is NOT set. If the connection isn't saved in NetworkManager, ensure may fail auth."
fi

# ---- helper: pretty print JSON if jq exists ----
pp_json() {
  if command -v jq >/dev/null 2>&1; then jq .; else cat; fi
}

# ---- helper: parse ok from JSON robustly ----
json_ok() {
  python3 -c 'import json,sys; data=json.load(sys.stdin); print("true" if data.get("ok") is True else "false")'
}

# ---- Step 1: status (before) ----
log "STEP1: status (before)"
python3 "$TOOL" --json status --iface "$IFACE" \
  | tee /tmp/wifi_nm_status_before.json \
  | pp_json

# ---- Step 2: ensure ----
log "STEP2: ensure target wifi"
ENSURE_ARGS=(--json ensure --iface "$IFACE" --ssid "$SSID" --timeout "$TIMEOUT" --band "$BAND")

if [[ -n "$BSSID" ]]; then
  ENSURE_ARGS+=(--bssid "$BSSID")
fi

# wifi_nm.py default is never-default unless --allow-default. Still pass for clarity if requested.
if [[ "$NEVER_DEFAULT" == "1" ]]; then
  ENSURE_ARGS+=(--never-default)
else
  ENSURE_ARGS+=(--allow-default)
fi

# password via env (preferred) if set
if [[ -n "${!PASSWORD_ENV:-}" ]]; then
  ENSURE_ARGS+=(--password-env "$PASSWORD_ENV")
fi

python3 "$TOOL" "${ENSURE_ARGS[@]}" \
  | tee /tmp/wifi_nm_ensure.json \
  | pp_json

OK="$(cat /tmp/wifi_nm_ensure.json | json_ok)"
if [[ "$OK" != "true" ]]; then
  echo "ERROR: ensure returned ok=false" >&2
  exit 1
fi

# ---- Step 3: cross-check link ----
log "STEP3: cross-check (iw link / nmcli / ip)"
log "iw dev $IFACE link:"
iw dev "$IFACE" link || true

log "nmcli dev status (wifi):"
nmcli dev status | sed -n '1,3p;/wifi/p' || true

log "ip addr (iface):"
ip -4 addr show "$IFACE" || true

log "routes referencing iface:"
ip route | grep -F "$IFACE" || true

if [[ -n "$BSSID" ]]; then
  if iw dev "$IFACE" link 2>/dev/null | grep -qiE "Connected to ${BSSID}"; then
    log "OK: Connected BSSID matches expected: $BSSID"
  else
    log "WARN: Connected BSSID does NOT obviously match expected ($BSSID). (Check 'iw link' output above)"
  fi
fi

# ---- Step 4: ping CPE (optional but recommended) ----
log "STEP4: ping CPE IP (basic L2/L3 sanity)"
if ping -c 2 -W 2 "$CPE_IP" >/dev/null 2>&1; then
  log "OK: ping CPE_IP=$CPE_IP success"
else
  log "WARN: ping CPE_IP=$CPE_IP failed (could be firewall/ICMP blocked or wrong LAN IP)"
fi

if [[ -n "$PING_TARGET" ]]; then
  log "STEP4b: ping target=$PING_TARGET"
  if ping -c 2 -W 2 "$PING_TARGET" >/dev/null 2>&1; then
    log "OK: ping $PING_TARGET success"
  else
    log "WARN: ping $PING_TARGET failed (may be expected if Wi-Fi is never-default or no internet on that path)"
  fi
fi

# ---- Step 5: status (after) ----
log "STEP5: status (after)"
python3 "$TOOL" --json status --iface "$IFACE" \
  | tee /tmp/wifi_nm_status_after.json \
  | pp_json

log "DONE: wifi_nm.py status/ensure basic validation complete."

