# Agent Runbook（給 AI/自動化助理）

目標：讓 Agent 以最少背景知識也能「照做必成功」。本頁刻意偏結構化、可複製貼上。

## 核心原則

- **平台參數以 systemd env 為準**；`manifest.yaml` 只提供 defaults，不可寫死平台值（WIFI_IFACE / PDU / CPE_DEV / PING_IFACE / TEST_PROFILE…）。
- 高風險動作（import/purge/stop/clear queue）要在紀錄中留下 run_id / 變更內容 / 備份檔名。

## 重要連結

- UI：`http://172.14.1.140:5173/`
- API base：`http://172.14.1.140:5173/api`

## 常用 API（最短路徑）

> 以平台提供的 CLI 或直接呼叫 API 均可；此處以既有 `charter_api_cli.py` 表達。

- 列 scripts：`python3 charter_api_cli.py scripts list`
- 找 script：`python3 charter_api_cli.py scripts find --suite <suite> --name <name>`
- 跑 script：`python3 charter_api_cli.py scripts run --suite <suite> --name <name>`
- 列 runs：`python3 charter_api_cli.py runs list --limit 50`
- 抓 log：`python3 charter_api_cli.py runs log --run-id <rid>`
- purge finished：`python3 charter_api_cli.py runs purge --older-than-days 0`

## Wi‑Fi 常見故障定位（iwd）

- 現象：可連 SSID、可 ping router，但 ping internet 失敗
  - 優先看：Wi‑Fi iface 是否缺 IPv4 default route（工具 `wifi_iwd.py` 已有補 default route 的修正邏輯）。
- 現象：腳本選到 `wlan0` 但實體是 `wlx...`
  - 正解：在 `charter-worker.service` 設 `WIFI_IFACE=<實際 iface>`；腳本不要硬寫。

## 交付紀錄（Agent 必填）

每次你做了會影響平台狀態的事情，至少留下：
- 日期/時間
- 影響範圍（suite/script/run_id）
- 你改了什麼（檔案路徑 + 備份名/sha）
- 重跑驗證 run_id + PASS/FAIL

