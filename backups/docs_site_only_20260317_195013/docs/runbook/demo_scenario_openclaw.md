# Demo 場景（工程向）— Charter Test Platform via OpenClaw

> 目標：用 15–20 分鐘讓工程同事看懂「平台怎麼跑、怎麼取證、怎麼改腳本、怎麼回溯」。

---

## 0) Demo 前準備（避免翻車）

- 平台（11F_140 範例）：`http://172.14.1.140:5173`
- 確認 worker 正常（必要時看 `journalctl -u charter-worker.service`）
- 避免把 secrets（NOC/SSH/Warehouse）展示在投影畫面或截圖

---

## 1) 文件站（SOP）先講清楚（4–5 分）

### 1.1 Runs SOP（2–3 分）

重點：
- **run_id 是所有追查/取證的索引**
- PASS/FAIL 不只看 UI，必要時抓 log / log-archive

常用：
```bash
export CHARTER_BASE="http://172.14.1.140:5173"
RID=1234

curl -sS "$CHARTER_BASE/api/runs?limit=50" | python3 -m json.tool
curl -sS "$CHARTER_BASE/api/runs/$RID/log" > run_${RID}_log.json

# 若 fail-hook 有產生 cpe logs
curl -sS "$CHARTER_BASE/api/runs/$RID/log-archives" | python3 -m json.tool
curl -fsSL "$CHARTER_BASE/api/runs/$RID/log-archive" -o run_${RID}_cpe_log.tar.gz

# 清理 finished runs + workdir
curl -sS -X DELETE "$CHARTER_BASE/api/runs/purge?older_than_days=0" | python3 -m json.tool
```

### 1.2 Script Change SOP（2 分）

固定流程（一定照做）：
1) Export 備份
2) 修改（manifest 或 code）
3) **同名（suite+name）先刪再匯入**（避免 `skipped:DUPLICATE`）
4) Run 驗證
5) Evidence（log / archive）

---

## 2) 跑一支 Smoke（展示 API 優先 + 摘要回報）（4–5 分）

建議用：
- `C00000004_NOC_API_basic_test`

```bash
export CHARTER_BASE="http://172.14.1.140:5173"
SCRIPT_ID=????

# 觸發 run
curl -sS -X POST "$CHARTER_BASE/api/scripts/$SCRIPT_ID/run" | python3 -m json.tool
```

成功標準：
- run 最終 `status=passed`
- log 內可看到關鍵欄位（例如 locationId / exit_code=0）

---

## 3) 需求轉折：把 C00000003 改成跑 3 cycles（7–8 分）

目標：把 `C00000003_WIFI_basic_test` 改成 `CYCLES=3`，並跑一次驗證。

### 3.1 找到 script_id（用名稱查，不記 id）

```bash
export CHARTER_BASE="http://172.14.1.140:5173"
NAME='C00000003_WIFI_basic_test'

curl -sS "$CHARTER_BASE/api/scripts?suite=sanity&q=$NAME" | python3 -m json.tool
```

### 3.2 Export 備份

```bash
SCRIPT_ID=123
mkdir -p backup_scripts
curl -fsSL "$CHARTER_BASE/api/scripts/$SCRIPT_ID/export" -o "backup_scripts/${NAME}_${SCRIPT_ID}.zip"
```

### 3.3 改 manifest（最乾淨）

```bash
# 先抓 manifest
curl -sS "$CHARTER_BASE/api/scripts/$SCRIPT_ID/manifest" | python3 -m json.tool > manifest.json

# 取出 content 欄位並修改：把 env.CYCLES 改成 '3'
#（示範時可用編輯器手動改，或由 OpenClaw 助理代改）
```

修改完後 PUT 回去：
```bash
curl -sS -X PUT "$CHARTER_BASE/api/scripts/$SCRIPT_ID/manifest" \
  -H 'Content-Type: application/json' \
  -d '{"content": "<貼上修改後 manifest yaml>"}' | python3 -m json.tool
```

> 備註：若你想保留原版不動，請用「Export → 改 zip → delete same name → import2」流程建立新 script。

### 3.4 Run 驗證

```bash
curl -sS -X POST "$CHARTER_BASE/api/scripts/$SCRIPT_ID/run" | python3 -m json.tool
```

成功標準：
- log/summary 能看出 cycle 執行了 3 次（或有等價的 wrapper 輸出）

---

## 4) 收尾（1–2 分）

一句話收斂：
- 「OpenClaw 讓 Charter 平台的跑測試、取證、改腳本變成 SOP；工程同事照做就能複製，遇到 fail 也能按 run_id 追查。」
