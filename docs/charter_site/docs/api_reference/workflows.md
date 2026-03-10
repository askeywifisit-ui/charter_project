# API Workflows（實戰工作流）

本頁提供幾個最常用的 API 操作工作流，讓維運/驗證同仁可以照做。

> 先設定 base：
```bash
export CHARTER_BASE="http://{{CONTROL_PC_IP}}:5173"
```

## 貼到 Telegram/聊天軟體時避免「連結預覽卡片」
某些聊天軟體會自動把 URL 變成預覽卡片。
- 最乾淨：送出前選「Disable link preview」
- 或把網址寫成不可點（加空格破壞連結），例如：
  - `http://{{CONTROL_PC_IP}} :5173/api/health`

---

## Workflow 1：匯入 → 執行 → 取 log

### 1) 匯入（import2）
```bash
curl -sS -X POST "$CHARTER_BASE/api/scripts/import2" \
  -F 'suite=sanity' \
  -F 'file=@./your_script.zip;type=application/zip' | jq .
```

### 2) 查到 script_id
```bash
curl -sS "$CHARTER_BASE/api/scripts?suite=sanity&q=YourScriptName" | jq .
```

### 3) Run
```bash
SCRIPT_ID=123
curl -sS -X POST "$CHARTER_BASE/api/scripts/$SCRIPT_ID/run" | jq .
# 會拿到 run_id
```

### 4) 取 log
```bash
RID=1234
curl -sS "$CHARTER_BASE/api/runs/$RID/log" > run_${RID}_log.json
```

---

## Workflow 2：Stop 卡住的 run
```bash
RID=1234
curl -sS -X POST "$CHARTER_BASE/api/runs/$RID/stop" | jq .
```

---

## Workflow 3：下載 fail 時的 cpe_log archive
```bash
RID=1234
curl -sS "$CHARTER_BASE/api/runs/$RID/log-archives" | jq .
curl -fsSL "$CHARTER_BASE/api/runs/$RID/log-archive" -o run_${RID}_cpe_log.tar.gz
```

---

## Workflow 4：清理 runs + workdir（常用）
> 會刪除已 finished 的 runs + 對應工作目錄。
```bash
curl -sS -X DELETE "$CHARTER_BASE/api/runs/purge?older_than_days=0" | jq .
```

先 dry-run：
```bash
curl -sS -X DELETE "$CHARTER_BASE/api/runs/purge?older_than_days=0&dry_run=1" | jq .
```
