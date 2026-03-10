# wifi_nm.py

- 位置（control PC）：`/home/da40/charter/tools/wifi_nm.py`

## Overview
`wifi_nm.py` 使用 **NetworkManager（nmcli）** 控制 Wi‑Fi，常作為 Wi‑Fi 測試的 fallback（或特定環境 iwd 不穩時改用）。

支援：
- `status` / `scan` / `ensure` / `disconnect` / `active`
- `--json` 輸出
- 需要時可 `--auto-start-nm`

## 常用範例
### ensure
```bash
export WIFI_PSK='{{PSK}}'
python3 /home/da40/charter/tools/wifi_nm.py --json ensure \
  --iface "{{WIFI_IFACE}}" \
  --ssid "{{SSID}}" \
  --password-env WIFI_PSK \
  --timeout 45 \
  --retries 2 \
  --auto-start-nm
```

### disconnect
```bash
python3 /home/da40/charter/tools/wifi_nm.py --json disconnect --iface "{{WIFI_IFACE}}"
```

## 常見問題 / 排除
- NM service 未啟動：用 `--auto-start-nm` 或先確認 systemctl
- SSID/PSK 來源：通常由 `cpe_ssh.py --cmd wifi-creds` 提供
