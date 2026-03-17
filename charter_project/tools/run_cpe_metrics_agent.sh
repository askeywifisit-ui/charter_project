#!/usr/bin/env bash
set -euo pipefail

# Python & agent path
BIN_PY="/home/da40/charter/apps/api/.venv/bin/python"
AGENT="/home/da40/charter/tools/cpe_metrics_agent_serial.py"

# cpe_info：只用來查密碼
CPE_INFO_BIN="${CPE_INFO_BIN:-/home/da40/charter/tools/cpe_info}"
CPE_INFO_TIMEOUT="${CPE_INFO_TIMEOUT:-10}"

# ===== 基本參數（可由 /etc/default/cpe-metrics-agent 覆蓋） =====
API="${CPE_AGENT_API:-http://127.0.0.1:8080}"
BAUD="${CPE_BAUD:-115200}"
USER="${CPE_USER:-root}"
IFACE="${CPE_IFACE:-eth0}"
TEMP_CMD="${CPE_TEMP_CMD:-cat /sys/class/thermal/thermal_zone4/temp}"
INTERVAL="${INTERVAL:-5}"
RUN_ID="${RUN_ID:-0}"
WITH_WIFI="${WITH_WIFI:-1}"
WITH_RADIO="${WITH_RADIO:-1}"

# ===== 1) 決定 console serial device =====
# 優先順序：
#   1. CPE_SERIAL（/etc/default 或 systemd Environment）
#   2. CPE_DEV  （跟 test manifest 同名的變數）
#   3. /dev/serial/by-id/ 底下 ASKEY console if02
#   4. /dev/serial/by-id/usb-FTDI_FT232R_USB_UART_B0008Z1P-if00-port0
#   5. 最後 fallback /dev/ttyUSB0
SER="${CPE_SERIAL:-${CPE_DEV:-}}"

# 3) 自動找 ASKEY console if02
if [[ -z "${SER}" ]]; then
  # 先試你現在已知的名字
  if [[ -e "/dev/serial/by-id/usb-ASKEY_ASKEY_Console_Board_FT4PGJN6-if02-port0" ]]; then
    SER="/dev/serial/by-id/usb-ASKEY_ASKEY_Console_Board_FT4PGJN6-if02-port0"
  else
    # 再試 general pattern（SN 不同也可以）
    for cand in /dev/serial/by-id/*ASKEY_ASKEY_Console_Board*if02-port0; do
      if [[ -e "$cand" ]]; then
        SER="$cand"
        break
      fi
    done
  fi
fi

# 4) 找不到 ASKEY，就改用 FTDI 那支
if [[ -z "${SER}" ]]; then
  if [[ -e "/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_B0008Z1P-if00-port0" ]]; then
    SER="/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_B0008Z1P-if00-port0"
  fi
fi

# 5) 最後保命 fallback
SER="${SER:-/dev/ttyUSB0}"

# ===== 2) 決定 console password =====
# 優先順序：
#   1. CPE_PASSWORD（/etc/default 或其它環境）
#   2. cpe_info --password
RAW_PASS="${CPE_PASSWORD:-}"

if [[ -z "${RAW_PASS}" ]] && [[ -x "$CPE_INFO_BIN" ]]; then
  if PASS_OUT=$(timeout "$CPE_INFO_TIMEOUT" "$CPE_INFO_BIN" --password 2>/dev/null); then
    [[ -n "$PASS_OUT" ]] && RAW_PASS="$PASS_OUT"
  fi
fi

PASS_OPT=()
if [[ -n "${RAW_PASS}" ]]; then
  PASS_OPT=(--password "$RAW_PASS")
fi

# ===== 3) 其它額外參數（WiFi、Radio、Device ID） =====
EXTRA=()
[[ "$WITH_WIFI" == "1" ]] && EXTRA+=("--with-wifi")
[[ "$WITH_RADIO" == "1" ]] && EXTRA+=("--with-radio")
if [[ -n "${CPE_DEVICE_ID:-}" ]]; then
  EXTRA+=("--device-id" "$CPE_DEVICE_ID")
fi

# ===== 4) 簡單 log（密碼打馬賽克） =====
if [[ -n "${RAW_PASS}" ]]; then
  pw_len=${#RAW_PASS}
  if (( pw_len > 5 )); then
    pw_masked="${RAW_PASS:0:3}***${RAW_PASS: -2}"
  else
    pw_masked="***"
  fi
else
  pw_masked="(empty)"
fi

echo "run_cpe_metrics_agent.sh: api=$API device=$SER baud=$BAUD iface=$IFACE interval=${INTERVAL}s run_id=$RUN_ID wifi=$WITH_WIFI radio=$WITH_RADIO password=$pw_masked" >&2

# ===== 5) 啟動 metrics agent =====
exec "$BIN_PY" "$AGENT" \
  --api "$API" \
  --device "$SER" --baud "$BAUD" \
  --user "$USER" "${PASS_OPT[@]}" \
  --iface "$IFACE" \
  --temp-cmd "$TEMP_CMD" \
  --interval "$INTERVAL" \
  --run-id "$RUN_ID" \
  "${EXTRA[@]}"

