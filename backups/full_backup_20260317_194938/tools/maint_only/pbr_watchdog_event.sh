#!/usr/bin/env bash
set -euo pipefail
SRC=${SRC:-192.168.1.2}
IF=${IF:-eno2}
GW=${GW:-192.168.1.1}
SUB=${SUB:-192.168.1.0/24}
T=${T:-100}
PF=${PF:-1000}
PT=${PT:-1001}

reapply() {
  # 介面要 up 且有 SRC 才處理
  if ip -4 addr show dev "$IF" | grep -q "$SRC"; then
    if ! ip route get 8.8.8.8 from "$SRC" 2>/dev/null | grep -q "via $GW dev $IF"; then
      echo "[pbr_watchdog] reapply PBR on $IF"
      /home/da40/charter/tools/pbr_cpe.py --src-ip "$SRC" --iface "$IF" --gw "$GW" \
        --subnet "$SUB" --table-id "$T" --prio-from "$PF" --prio-to "$PT" setup
    fi
  fi
}

# 啟動時先檢一次
reapply

# 監看 link/address 事件
ip monitor link address dev "$IF" | while read -r _; do
  reapply
done

