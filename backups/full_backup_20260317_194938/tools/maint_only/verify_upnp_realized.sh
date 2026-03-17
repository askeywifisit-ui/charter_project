#!/usr/bin/env bash
set -euo pipefail

BASE="https://piranha-int.tau.dev-charter.net"
CUSTOMER_ID="65a740cc4ac901000ade23a7"
EMAIL="c-xin.guo@charter.com"
PASSWORD="Xin@Plume"

LOCATION_ID="693285aaa5dc9d0f5da63310"
CLI="./noc_api_cli.py"

INTERVAL_SEC=15
TIMEOUT_SEC=300
START_TS="$(date +%s)"

echo "[INFO] login -> get token"
TOKEN="$(python3 "$CLI" --base "$BASE" --customer-id "$CUSTOMER_ID" --email "$EMAIL" --password "$PASSWORD" login 2>&1 | tail -n 1 | tr -d '\r')"
if [[ -z "$TOKEN" ]]; then
  echo "[ERROR] login returned empty token"
  exit 2
fi
echo "[INFO] token acquired (len=${#TOKEN})"
echo "[INFO] start polling upnp-status: location_id=$LOCATION_ID, interval=${INTERVAL_SEC}s, timeout=${TIMEOUT_SEC}s"
echo

while true; do
  NOW_TS="$(date +%s)"
  ELAPSED=$(( NOW_TS - START_TS ))

  if (( ELAPSED > TIMEOUT_SEC )); then
    echo
    echo "[FAIL] timeout after ${ELAPSED}s (modeRealized still not true)"
    echo "[INFO] last raw output:"
    python3 "$CLI" --base "$BASE" --customer-id "$CUSTOMER_ID" --token "$TOKEN" \
      upnp-status --location-id "$LOCATION_ID" 2>&1 || true
    exit 1
  fi

  # 這裡不要讓單次失敗就讓整支 script 掛掉，所以暫時關掉 set -e
  set +e
  OUT="$(python3 "$CLI" --base "$BASE" --customer-id "$CUSTOMER_ID" --token "$TOKEN" \
    upnp-status --location-id "$LOCATION_ID" 2>&1)"
  RC=$?
  set -e

  if [[ $RC -ne 0 ]]; then
    echo "[T+${ELAPSED}s] [WARN] upnp-status rc=$RC"
    echo "  raw: ${OUT:0:300}"
    sleep "$INTERVAL_SEC"
    continue
  fi

  # OUT 不是 JSON（或是空）就直接印 raw 讓你看到
  PARSED="$(python3 - << 'PY'
import json,sys
s=sys.stdin.read().strip()
if not s:
  print("NOT_JSON:EMPTY")
  raise SystemExit(0)
try:
  j=json.loads(s)
except Exception as e:
  print("NOT_JSON:" + str(e))
  raise SystemExit(0)
enabled=j.get("enabled")
mode=j.get("mode")
real=j.get("modeRealized")
print(f"enabled={enabled} mode={mode} modeRealized={real}")
print("REALIZED_TRUE" if real is True else "REALIZED_FALSE")
PY
<<<"$OUT")"

  if [[ "$PARSED" == NOT_JSON:* ]]; then
    echo "[T+${ELAPSED}s] [WARN] upnp-status output is not JSON"
    echo "  raw: ${OUT:0:300}"
    sleep "$INTERVAL_SEC"
    continue
  fi

  LINE1="$(echo "$PARSED" | head -n1)"
  FLAG="$(echo "$PARSED" | tail -n1)"

  echo "[T+${ELAPSED}s] $LINE1"

  if [[ "$FLAG" == "REALIZED_TRUE" ]]; then
    echo
    echo "[PASS] modeRealized became true after ${ELAPSED}s"
    exit 0
  fi

  sleep "$INTERVAL_SEC"
done

