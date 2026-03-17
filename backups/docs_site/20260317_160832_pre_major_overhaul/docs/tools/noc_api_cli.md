# noc_api_cli.py

- 位置（control PC）：`/home/da40/charter/tools/noc_api_cli.py`

## Overview
`noc_api_cli.py` 是 Charter 平台用來操作 **NOC/Cloud API** 的工具模組，常見用途：
- login 取得 token
- 依 `customer_id + node_id` 查 `location_id`
- enable/disable SSH
- speedtest / reboot / DHCP reservation / Wi‑Fi radio toggle 等

> 多數 scripts 是用「import 方式」呼叫此模組，而不是把它當 CLI 直接執行。

## 你需要準備的設定（最常見）
- `PROFILES_FILE=/home/da40/charter/.secrets/noc_profiles.json`
- `NOC_PROFILE=SPECTRUM_INT`
- `CUSTOMER_ID=...`

詳見：Hand-off → **NOC Profile / Secrets**。

## 常見失敗
### `noc-context timeout`
- 症狀：`Read timed out (read timeout=20)`
- 原因：NOC endpoint 慢、出口網路/DNS/Proxy
- 建議：retry/backoff、拉長 timeout、確認 control PC 出口

## 交付建議
- 不要把 NOC 帳密寫進 repo
- profiles 檔用最小權限與輪替策略
