# 驗證步驟（快速驗證）

> 目標：對方在替換環境後，快速確認平台可用。

先設定 base：
```bash
export CHARTER_BASE="http://{{CONTROL_PC_IP}}:5173"
```

## 1) Health
```bash
curl -sS "$CHARTER_BASE/api/health" | jq .
```

## 2) Scripts
```bash
curl -sS "$CHARTER_BASE/api/scripts?suite=sanity" | jq '.[0:5]'
```

## 3) Worker
```bash
curl -sS "$CHARTER_BASE/api/runs/worker/status" | jq .
```

## 4) Run 一條最小 sanity（例：Wi‑Fi basic 或 SSH basic）
1) 先找 script_id：
```bash
curl -sS "$CHARTER_BASE/api/scripts?suite=sanity&q=C00000003" | jq .
```
2) 執行：
```bash
SCRIPT_ID=123
curl -sS -X POST "$CHARTER_BASE/api/scripts/$SCRIPT_ID/run" | jq .
```
3) 取 log：
```bash
RID=1234
curl -sS "$CHARTER_BASE/api/runs/$RID/log" > run_${RID}_log.json
```

## 5) 失敗時：下載 cpe_log archive（若有）
```bash
RID=1234
curl -sS "$CHARTER_BASE/api/runs/$RID/log-archives" | jq .
curl -fsSL "$CHARTER_BASE/api/runs/$RID/log-archive" -o run_${RID}_cpe_log.tar.gz
```

## 6) 清理 runs/workdir（可選）
```bash
curl -sS -X DELETE "$CHARTER_BASE/api/runs/purge?older_than_days=0" | jq .
```
