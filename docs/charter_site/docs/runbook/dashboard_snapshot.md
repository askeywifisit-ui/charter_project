# Dashboard 一鍵抓取（API Snapshot）

本頁提供一個「不用爬網頁」的方式，用 API 一次抓回 Dashboard 主要資料（CPE 狀態、metrics 圖表、Wi‑Fi、pass rate、event log）。

## 什麼時候用
- 要回報目前 CPE 狀態（Internet/Cloud/IPv4/MAC/FW/SN）
- 要留存一份 dashboard 證據（JSON 檔案）方便後續分析
- 要做 daily report / trend 分析

## 腳本位置
- `workspace/scripts/snapshot_dashboard.py`

## 用法
```bash
cd /Users/csit/.openclaw/workspace
python3 scripts/snapshot_dashboard.py --base http://172.14.1.140:5173
```

參數：
- `--window-hours 24|48|72`：dashboard metrics 視窗
- `--events eventlog|runs|both`：event 來源
- `--n-metrics N`：抓回最新 metrics 點數

## 會抓哪些 API
- `GET /api/cpe/info`
- `GET /api/cpe/status/latest`
- `GET /api/dashboard/metrics`
- `GET /api/metrics/latest`
- `GET /api/wifi/stations/count`
- `GET /api/wifi/radio/state`

## 輸出
腳本會建立資料夾：`dashboard_snapshot_<timestamp>/`，內含：
- `cpe_info.json`
- `cpe_status_latest.json`
- `dashboard_metrics.json`
- `metrics_latest.json`
- `wifi_stations_count.json`
- `wifi_radio_state.json`
- `summary.txt`（多行摘要）
- `one_line.txt`（一行摘要）

### 一行摘要（方便貼群組）
腳本 stdout 會先印出一行類似：
```text
DashboardSnapshot Internet=Connected Cloud=Connected IPv4=... MAC=... FW=... Model=... SN=... HB_age=...s
```

## 範例（本環境一次抓取）
> 例：`dashboard_snapshot_20260225_192236/summary.txt`

```text
base=http://172.14.1.140:5173
ts=20260225_192236
Internet=Connected
Cloud=Connected
IPv4=172.14.1.199
MAC=90:D3:CF:EB:6A:4D
FW=1.3.0-12-782766-g202512101845-SBE1V1K-development
Model=SBE1V1K
SN=70KW2512417000F
HB_age=0
pass_rate={"stability": 0.0, "sanity": 0.0, "regression": 0.0}
```
