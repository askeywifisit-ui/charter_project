# Demo 場景 — Charter Test Platform via OpenClaw

> 目標：讓被移轉者能在 15-20 分鐘內看懂「平台怎麼跑、怎麼取證、怎麼改腳本」。

---

## 🎯 我是誰？

| 問題 | 答案 |
|------|------|
| 這是什麼？ | Charter 自動化測試平台 |
| 給誰看？ | 被移轉的工程師 |
| 要多久？ | 約 15-20 分鐘 |

---

## ⏱️ 時間分配

| 步驟 | 時間 | 重點 |
|------|------|------|
| 0. Demo 整備 | 3 分 | 準備環境、檢查狀態 |
| 1. 平台介紹 | 4 分 | GUI 操作 + API 指令 |
| 2. 跑 Smoke 測試 | 4 分 | 實際跑一支給你看 |
| 3. 改腳本驗證 | 7 分 | 實際操作給你看 |
| 4. 收尾 | 2 分 | 總結 |

---

## ⚠️ Step 0：Demo 整備（3 分）

### Demo 前一定要確認

| 項目 | 確認方式 |
|------|----------|
| 平台可連 | http://172.14.1.140:5173 能開 |
| Worker 正常 | `journalctl -u charter-worker.service` |
| 文件站可連 | http://172.14.1.140:8000 能開 |
| 測試腳本存在 | 確認 C00000003、C00000004 可用 |

---

## Step 1：平台介紹（4 分）

### 1.1 GUI 操作（用瀏覽器）

**位置**：http://172.14.1.140:5173

| 功能 | 怎麼做 |
|------|--------|
| 看腳本 | 點「Suites」→ 選 sanity/stability |
| 跑測試 | 找到腳本 → 點「Run」按鈕 |
| 看結果 | 點「Runs」→ 看 PASS/FAIL |
| 看 Log | 點某一筆 Run → 展開看詳細 |

### 1.2 API 操作（用指令）

| 功能 | 指令 |
|------|------|
| 查腳本列表 | `curl "$CHARTER_BASE/api/scripts?suite=sanity"` |
| 查執行結果 | `curl "$CHARTER_BASE/api/runs?limit=10"` |
| 執行腳本 | `curl -X POST "$CHARTER_BASE/api/scripts/5228/run"` |
| 看單筆結果 | `curl "$CHARTER_BASE/api/runs/7500"` |
| 下載 Log | `curl "$CHARTER_BASE/api/runs/7500/log" -o log.json` |
| 刪除舊資料 | `curl -X DELETE "$CHARTER_BASE/api/runs/purge?older_than_days=7"` |

---

## Step 2：跑 Smoke 測試（4 分）

### 示範腳本

- **C00000004_NOC_API_basic_test**（推薦，最簡單）

### 一步一步做

**Step 2.1 查腳本 ID**
```bash
curl -sS "$CHARTER_BASE/api/scripts?suite=sanity&q=NOC_API" | jq .
```

**Step 2.2 執行**
```bash
SCRIPT_ID=5228
curl -sS -X POST "$CHARTER_BASE/api/scripts/$SCRIPT_ID/run" | jq .
```

**Step 2.3 看結果**
```bash
# 刷結果
curl -sS "$CHARTER_BASE/api/runs?limit=3" | jq .
```

**成功標準**：
- status = `passed`
- exit_code = 0

---

## Step 3：改腳本驗證（7 分）

### 目標

把 `C00000003_WIFI_basic_test` 改成跑 **3 cycles**

### 3.1 Export 備份
```bash
SCRIPT_ID=5227
curl -fsSL "$CHARTER_BASE/api/scripts/$SCRIPT_ID/export" -o backup.zip
```

### 3.2 修改 manifest
```bash
# 抓 manifest
curl -sS "$CHARTER_BASE/api/scripts/$SCRIPT_ID/manifest" | jq .content -r > manifest.yaml

# 改 CYCLES=3
sed -i 's/CYCLES: 1/CYCLES: 3/' manifest.yaml
```

### 3.3 回存
```bash
CONTENT=$(cat manifest.yaml | jq -Rs .)
curl -sS -X PUT "$CHARTER_BASE/api/scripts/$SCRIPT_ID/manifest" \
  -H 'Content-Type: application/json' \
  -d "{\"content\": $CONTENT}" | jq .
```

### 3.4 Run 驗證
```bash
curl -sS -X POST "$CHARTER_BASE/api/scripts/$SCRIPT_ID/run" | jq .
```

---

## Step 4：收尾（2 分）

### 一句話總結

> 「平台讓跑測試、取證、改腳本變成 SOP；照著做就能複製，fail 了也能用 run_id 追查。」

---

## ❓ 遇到問題？

| 問題 | 處理方式 |
|------|----------|
| Worker 沒反應 | 檢查 `journalctl -u charter-worker.service` |
| DUPLICATE 錯誤 | 匯入前先刪除同名 script |
| 不知道腳本 ID | 用 `?q=關鍵字` 搜尋 |

---

## 📞 支援

- 文件站：http://172.14.1.140:8000/
- API 文件：/api_reference/

---

## 相關頁面

- [Runs 操作](../user_guide/runs/)
- [Scripts 管理](../user_guide/scripts/)
- [API Reference](../api_reference/)
