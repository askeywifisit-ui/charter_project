# wifi_iwd.py

- 位置（control PC）：`/home/da40/charter/tools/wifi_iwd.py`

## Overview
`wifi_iwd.py` 使用 **iwd/iwctl + DHCP** 控制 Wi‑Fi 連線流程，常用於 sanity/stability 的 Wi‑Fi client 測試。

支援：
- `scan` / `status` / `ensure`（連線）/ `disconnect`
- takeover/restore（避免 NetworkManager/wpa_supplicant 競態）
- 進階：PBR（policy based routing）

## 介面（節錄自 --help）
```text
python3 /home/da40/charter/tools/wifi_iwd.py --help
```
常用 flags：
- `--iface <iface>`（必填）
- `--ssid <ssid>`（ensure 時必填）
- `--password-env WIFI_PSK`（避免把 PSK 寫在命令列）
- `--timeout <sec>` / `--dhcp-timeout <sec>`
- `--takeover` / `--restore-nm` / `--unmanaged`

## 常用範例（建議照抄）
### 1) scan
```bash
python3 /home/da40/charter/tools/wifi_iwd.py --iface "{{WIFI_IFACE}}" scan --json
```

### 2) ensure（連線 + DHCP）
```bash
export WIFI_PSK='{{PSK}}'
python3 /home/da40/charter/tools/wifi_iwd.py --json ensure \
  --iface "{{WIFI_IFACE}}" \
  --ssid "{{SSID}}" \
  --password-env WIFI_PSK \
  --timeout 45 \
  --takeover --restore-nm --unmanaged
```

### 3) disconnect
```bash
python3 /home/da40/charter/tools/wifi_iwd.py --json disconnect --iface "{{WIFI_IFACE}}"
```

## 常見問題 / 排除
- `WIFI_IFACE` 不同：外部單位一定要替換（Hand-off → 網卡判定指南）
- NM/iwd 競態：建議用 `--takeover`
- 多路由誤判：必要時改用 PBR 參數或指定 ping 介面
