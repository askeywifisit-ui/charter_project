#!/usr/bin/env bash
set -euo pipefail

# ===== NOC 連線設定 =====
NOC_BASE="https://piranha-int.tau.dev-charter.net"
NOC_EMAIL="c-xin.guo@charter.com"
NOC_PASSWORD="Xin@Plume"
CUSTOMER_ID="682d4e5179b80027cd6fb27e"

# 預設 node-id，如要換機器直接在執行時帶參數
NODE_ID="${1:-90d3cfeb6a4d}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI="python3 ${SCRIPT_DIR}/noc_api_cli.py"

echo "=== 測試 UPNP CLI 工具 ==="
echo "NODE_ID = ${NODE_ID}"
echo

# 全域共用參數（這些是 argparse 的 global options）:contentReference[oaicite:2]{index=2}
COMMON_GLOBAL_ARGS=(
  --base "${NOC_BASE}"
  --email "${NOC_EMAIL}"
  --password "${NOC_PASSWORD}"
  --customer-id "${CUSTOMER_ID}"
)

echo "### Step 0: 把 node-id 轉成 location-id"
LOCATION_ID="$(
  ${CLI} \
    "${COMMON_GLOBAL_ARGS[@]}" \
    get-location \
    --node-id "${NODE_ID}"
)"
echo "LOCATION_ID = ${LOCATION_ID}"
echo

echo "### Step 1: 查目前 UPNP 狀態"
${CLI} \
  "${COMMON_GLOBAL_ARGS[@]}" \
  upnp-status \
  --location-id "${LOCATION_ID}"
echo

echo "### Step 2: 設成 enable 再查狀態"
${CLI} \
  "${COMMON_GLOBAL_ARGS[@]}" \
  upnp-disable \
  --location-id "${LOCATION_ID}"

${CLI} \
  "${COMMON_GLOBAL_ARGS[@]}" \
  upnp-status \
  --location-id "${LOCATION_ID}"
echo


echo "=== 測試完成 ==="

