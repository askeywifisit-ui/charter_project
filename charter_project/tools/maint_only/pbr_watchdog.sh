#!/usr/bin/env bash
set -euo pipefail
SRC=192.168.1.2
IF=eno2
GW=192.168.1.1
SUB=192.168.1.0/24
T=100
PF=1000
PT=1001

while true; do
  # 介面要 UP 且已拿到 SRC（避免還沒拿到 IP 亂設）
  if ip -4 addr show dev "$IF" | grep -q "$SRC"; then
    if ! ip route get 8.8.8.8 from "$SRC" 2>/dev/null | grep -q "via $GW dev $IF"; then
      echo "[pbr_watchdog] reapply PBR on $IF"
      /home/da40/charter/tools/pbr_cpe.py --src-ip "$SRC" --iface "$IF" --gw "$GW" \
        --subnet "$SUB" --table-id "$T" --prio-from "$PF" --prio-to "$PT" setup
    fi
  fi
  sleep 2
done

