# Dashboard 一鍵抓取

> 目標：不用爬網頁，一次抓回完整 Dashboard 資料。

---

## 🎯 我是誰？

| 問題 | 答案 |
|------|------|
| 這是什麼？ | 一鍵抓取 CPE 狀態的工具 |
| 誰要看？ | 需要回報狀態的人 |
| 什麼時候用？ | Daily report、故障分析、留存證據 |

---

## ⏱️ 什麼時候用？

| 場景 | 為什麼要用 |
|------|------------|
| 回報 CPE 狀態 | Internet/Cloud/IPv4/MAC/FW/SN 一次抓回 |
| 做 Daily Report | 留存證據方便後續分析 |
| 趨勢分析 | 長期收集 metrics |

---

## Step 1：執行抓取

### 指令
```bash
cd /Users/csit/.openclaw/workspace
python3 scripts/snapshot_dashboard.py --base http://172.14.1.140:5173
```

### 可選參數

| 參數 | 說明 | 預設 |
|------|------|------|
| `--window-hours` | Metrics 視窗（小時） | 24 |
| `--events` | Event 來源 | eventlog |
| `--n-metrics` | 最新 metrics 點數 | 10 |

### 範例
```bash
# 抓 48 小時 metrics
python3 scripts/snapshot_dashboard.py --base http://172.14.1.140:5173 --window-hours 48
```

---

## Step 2：輸出結果

### 資料夾結構
```
dashboard_snapshot_<timestamp>/
├── cpe_info.json           # CPE 基本資訊
├── cpe_status_latest.json # 最新狀態
├── dashboard_metrics.json  # Dashboard metrics
├── metrics_latest.json     # 最新 metrics
├── wifi_stations_count.json # Wi-Fi station 數量
├── wifi_radio_state.json  # Wi-Fi radio 狀態
├── summary.txt            # 多行摘要
└── one_line.txt          # 一行摘要
```

---

## Step 3：解讀結果

### 一行摘要（方便貼群組）

```
DashboardSnapshot Internet=Connected Cloud=Connected IPv4=172.14.1.199 MAC=90:D3:CF:EB:6A:4D FW=1.3.0-12 SN=70KW2512417000F HB_age=0s
```

### 欄位說明

| 欄位 | 意思 |
|------|------|
| Internet | CPE 對外連線狀態 |
| Cloud | 雲端連線狀態 |
| IPv4 | WAN IP |
| MAC | 設備 MAC |
| FW | 韌體版本 |
| SN | 序號 |
| HB_age | 最後 heartbeat 距今秒數 |

### Summary 範例

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

---

## 📡 會抓哪些 API？

| API | 用途 |
|-----|------|
| `/api/cpe/info` | CPE 基本資訊 |
| `/api/cpe/status/latest` | 最新狀態 |
| `/api/dashboard/metrics` | Dashboard metrics |
| `/api/metrics/latest` | 最新 metrics |
| `/api/wifi/stations/count` | Wi-Fi 連線數 |
| `/api/wifi/radio/state` | Wi-Fi Radio 狀態 |

---

## ❓ 遇到問題？

| 問題 | 處理 |
|------|------|
| 抓不到資料 | 確認平台正常運作 |
| 格式錯誤 | 檢查 JSON 是否有斷線 |

---

## 📞 支援

- 相關頁面：/runbook/operations/, /user_guide/runs/
