# Agent Runbook（OpenClaw 測試助理專用）

> 目標：讓 AI 助理以最少背景知識也能「照做必成功」。

---

## 🎯 我是誰？

| 問題 | 答案 |
|------|------|
| 這是什麼？ | Charter 平台操作手冊 |
| 誰要看？ | OpenClaw AI 助理 |
| 怎麼用？ | 照著指令複製貼上 |

---

## ⚠️ 核心原則

1. **平台參數以 systemd env 為準**
   - `manifest.yaml` 只提供 defaults
   - 不可寫死：WIFI_IFACE / PDU / CPE_DEV / PING_IFACE / TEST_PROFILE

2. **高風險動作要記錄**
   - import / purge / stop / clear queue
   - 必須留下：run_id、變更內容、備份檔名

---

## 📍 重要連結

| 服務 | 網址 |
|------|------|
| Control UI | http://172.14.1.140:5173/ |
| API Base | http://172.14.1.140:5173/api |
| 文件站 | http://172.14.1.140:8000/ |

---

## 📋 常用指令（複製貼上）

### 查詢腳本

```bash
# 列出所有腳本
curl -sS "http://172.14.1.140:5173/api/scripts?limit=100" | jq .

# 找特定腳本（用名稱）
curl -sS "http://172.14.1.140:5173/api/scripts?suite=sanity&q=DHCP" | jq .

# 用 script_id 查
curl -sS "http://172.14.1.140:5173/api/scripts/5225" | jq .
```

### 執行腳本

```bash
# 執行腳本
curl -sS -X POST "http://172.14.1.140:5173/api/scripts/5225/run" | jq .

# 看執行結果
curl -sS "http://172.14.1.140:5173/api/runs?limit=10" | jq .
```

### 看 Log

```bash
# 下載 log
curl -sS "http://172.14.1.140:5173/api/runs/7500/log" -o run_7500_log.json

# 看狀態
curl -sS "http://172.14.1.140:5173/api/runs/7500" | jq .
```

### 清理

```bash
# 清理已完成 runs（全部）
curl -sS -X DELETE "http://172.14.1.140:5173/api/runs/purge?older_than_days=0" | jq .

# 清理 7 天前
curl -sS -X DELETE "http://172.14.1.140:5173/api/runs/purge?older_than_days=7" | jq .
```

### Import / Export

```bash
# Export 腳本
curl -sS "http://172.14.1.140:5173/api/scripts/5225/export" -o backup.zip

# Import 腳本
curl -sS -X POST "http://172.14.1.140:5173/api/scripts/import2" \
  -F "suite=sanity" \
  -F "file=@./my_script.zip" | jq .

# Delete 腳本
curl -sS -X DELETE "http://172.14.1.140:5173/api/scripts/5225" | jq .
```

---

## 🔧 Wi-Fi 故障定位（iwd）

### 問題：可連 SSID、可 ping router，但 ping internet 失敗

**優先檢查**：Wi-Fi iface 是否缺 IPv4 default route

**解決**：`wifi_iwd.py` 已有補 default route 的邏輯

### 問題：腳本選到 `wlan0` 但實體是 `wlx...`

**正解**：在 `charter-worker.service` 設 `WIFI_IFACE=<實際 iface>`

---

## 📝 交付紀錄（必填）

每次做了影響平台狀態的事，至少留下：

| 欄位 | 範例 |
|------|------|
| 日期/時間 | 2026-03-18 14:00 |
| 影響範圍 | suite=sanity, script_id=5225 |
| 改了什麼 | 改了 manifest.yaml CYCLES=3 |
| 備份檔名 | backup_5225_20260318.zip |
| 驗證結果 | run_id=7500, PASS |

---

## ❓ 遇到問題？

| 問題 | 處理 |
|------|------|
| Worker 沒反應 | 檢查 `journalctl -u charter-worker.service` |
| Run 一直 queue | 確認 worker 狀態 `/api/runs/worker/status` |
| DUPLICATE 錯誤 | Import 前先刪除同名 script |
| Log 抓不到 | 確認 run 已經 finished |

---

## 📞 支援

- 文件站：http://172.14.1.140:8000/
- 相關頁面：/user_guide/runs/, /user_guide/scripts/
