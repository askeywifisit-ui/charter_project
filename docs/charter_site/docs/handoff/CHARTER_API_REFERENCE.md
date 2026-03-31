# Charter API 完整參考手冊

> 本檔案是 Charter 測試平台 API 的完整參考
> 
> **最後更新：** 2026-03-31

---

## 🌐 Base URL

| 環境 | URL |
|------|-----|
| **API** | `http://172.14.1.140:5173/api` |
| **Web UI** | `http://172.14.1.140:5173` |

設定環境變數：
```bash
export CHARTER_BASE="http://172.14.1.140:5173/api"
```

---

## 🔧 常用 HTTP Method

| Method | 用途 |
|--------|------|
| GET | 取得資料 |
| POST | 執行、建立資源 |
| PUT | 更新資源 |
| DELETE | 刪除資源 |

---

## 📊 Scripts API

### 取得所有腳本
```bash
GET /api/scripts
```

### 取得特定腳本
```bash
GET /api/scripts/{script_id}
```

### 取得腳本列表（依 suite 過濾）
```bash
GET /api/scripts?suite=sanity
GET /api/scripts?suite=stability
```

### 觸發腳本執行
```bash
POST /api/scripts/{script_id}/run
```

### 匯入腳本
```bash
POST /api/scripts/import
```

### 匯出腳本
```bash
GET /api/scripts/{script_id}/export
```

---

## 🧪 Runs API

### 取得所有測試記錄
```bash
GET /api/runs?limit=50
GET /api/runs?status=running
GET /api/runs?status=passed
GET /api/runs?status=failed
```

### 取得特定測試
```bash
GET /api/runs/{run_id}
```

### 取得測試日誌
```bash
GET /api/runs/{run_id}/log
```

### 取得 Log Archive
```bash
GET /api/runs/{run_id}/log-archive?name=xxx
```

### 停止測試
```bash
POST /api/runs/{run_id}/stop
```

### 停止所有測試
```bash
POST /api/runs/stop
```

### 刪除測試
```bash
DELETE /api/runs/{run_id}
```

### 清除舊測試（Purge）
```bash
DELETE /api/runs/purge?older_than_days=7
```

---

## 💓 Health API

### 健康檢查
```bash
GET /api/health
```
**回應：** `{"ok": true}`

---

## 📈 Dashboard / Metrics

### 取得 Dashboard 指標
```bash
GET /api/dashboard/metrics?window_hours=24
```

### WiFi 連線數
```bash
GET /api/wifi/stations/count
```

### WiFi  Radio 狀態
```bash
GET /api/wifi/radio/state
```

### CPE 最新狀態
```bash
GET /api/cpe/status/latest
```

### CPE 資訊
```bash
GET /api/cpe/info
```

---

## 🛠️ Worker API

### Worker 狀態
```bash
GET /api/worker/state
GET /api/worker
```

### 清除事件日誌
```bash
POST /api/event-log/clear
```

---

## ⚠️ HTTP 狀態碼

| 狀態碼 | 意義 | 常見原因 |
|--------|------|----------|
| 200 | OK | 請求成功 |
| 400 | Bad Request | 格式錯誤、缺少欄位 |
| 404 | Not Found | 資源不存在 |
| 405 | Method Not Allowed | 用錯 HTTP method |
| 409 | Conflict | 資源衝突 |
| 422 | Unprocessable Entity | 驗證失敗 |
| 5xx | Server Error | 服務異常 |

---

## 🔍 常用除錯指令

### 健康檢查
```bash
curl -sS "$CHARTER_BASE/api/health" | jq .
```

### 查看所有服務狀態
```bash
curl -sS "$CHARTER_BASE/api/runs/worker/status" | jq .
```

### 查看腳本列表
```bash
curl -sS "$CHARTER_BASE/api/scripts?suite=sanity" | jq .
```

### 觸發測試並追蹤
```bash
# 觸發
RUN_ID=$(curl -sS -X POST "$CHARTER_BASE/api/scripts/5225/run" | jq -r '.run_id')

# 等待完成
while true; do
  STATUS=$(curl -sS "$CHARTER_BASE/api/runs/$RUN_ID" | jq -r '.status')
  echo "Status: $STATUS"
  if [ "$STATUS" != "running" ] && [ "$STATUS" != "queued" ]; then
    break
  fi
  sleep 5
done
```

### 下載 Log Archive
```bash
curl -sS "$CHARTER_BASE/api/runs/{run_id}/log-archive?name=output" -o output.zip
```

---

## 📝 Scripts 快速對照表

### Sanity Suite（基本測試）
| Script ID | 名稱 |
|-----------|------|
| 5225 | C00000001_SSH_basic_test |
| 5226 | C00000002_SSH_disable_test |
| 5227 | C00000003_WIFI_basic_test |
| 5228 | C00000004_NOC_API_basic_test |
| 5229 | C15806902_WLAN_Client_connects_successfully_over_Default_SSID |
| ... | ... |

### Stability Suite（穩定性測試）
| Script ID | 名稱 |
|-----------|------|
| 5116 | A2844344_Continuously_executing_reboot |
| 5117 | C15806945_WiFi_radio_enable_disable_longrun |
| 5119 | C24541454_Multiple_reboot_stress |
| 5120 | C24541455_Multiple_speedtest |
| 5121 | C4123492_IPv4_Stability_Test_from_LAN_Client |
| ... | ... |

---

## ⚡ 觸發測試範例

### 觸發單一腳本
```bash
curl -sS -X POST "$CHARTER_BASE/api/scripts/5259/run"
# 回應: {"ok":true,"run_id":7937}
```

### 批次觸發（Shell Script）
```bash
#!/bin/bash
for id in 5116 5117 5119 5120 5121; do
  result=$(curl -sS -X POST "$CHARTER_BASE/api/scripts/$id/run")
  echo "Script $id: $result"
done
```

### 停止所有執行中的測試
```bash
curl -sS -X POST "$CHARTER_BASE/api/runs/stop"
```

### 清除 7 天前的測試記錄
```bash
curl -sS -X DELETE "$CHARTER_BASE/api/runs/purge?older_than_days=7"
```

---

## 🔐 測試狀態說明

| 狀態 | 意義 |
|------|------|
| `queued` | 等待執行 |
| `running` | 執行中 |
| `passed` | 通過 |
| `failed` | 失敗 |
| `error` | 錯誤 |

---

## 📁 Log Archive 結構

測試執行後的輸出檔案：
- `output.gz` - 主要輸出
- `cpe_metrics.json` - CPE 數據
- `cpe_status.json` - CPE 狀態
- `speedtest.json` - 速度測試結果

---

## 🤖 與外部系統整合

### NOC API
設定檔：`/home/da40/charter/.secrets/noc_profiles.json`

修改後需重啟：
```bash
sudo systemctl restart charter-worker
```

---

*本文件由 Alice (DA40) 整理*
