# Runs

對應 UI：`/runs`

## GET `/api/runs`
- 用途：列出 runs
- Query:
  - `limit: int`（預設 200）
- 回應：`RunRow[]`
  - `id, status, script, suite, created_at, started_at, finished_at`

### curl
```bash
curl -sS "$CHARTER_BASE/api/runs?limit=50" | jq .
```

## GET `/api/runs/{rid}/log`
- 用途：取某 run 的 log（前端會 stringify 顯示）

### curl
```bash
RID=1234
curl -sS "$CHARTER_BASE/api/runs/$RID/log" > run_${RID}_log.json
# 如果回傳不是 JSON array 而是字串，仍可直接看檔案
tail -n 50 run_${RID}_log.json
```

### 常見錯誤/注意
- log 內容格式有兩種：
  - JSON array（結構化 log）
  - 或單一字串（包含多行）

## POST `/api/runs/{rid}/stop`
## POST `/api/runs/stop?id={rid}`
- 用途：停止 run
- 行為（依 status）：
  - queued → 直接標 error + summary=stopped by user
  - starting/running → 標記 stopping
  - 其它 → noop
- 回應：`{"ok": true, "mode": "...", ...}`

### curl
```bash
RID=1234
curl -sS -X POST "$CHARTER_BASE/api/runs/$RID/stop" | jq .
# 或（舊路徑）
curl -sS -X POST "$CHARTER_BASE/api/runs/stop?id=$RID" | jq .
```

## DELETE `/api/runs/{rid}`
- 用途：刪除 run（DB）+ 刪除工作目錄（預設 WORK_BASE/run_{id}）

### curl
```bash
RID=1234
curl -sS -X DELETE "$CHARTER_BASE/api/runs/$RID" | jq .
```

### 注意
- 具破壞性（會刪 DB + 工作目錄），建議先取 log/下載 archive。

## DELETE `/api/runs/purge`
- 用途：批次清理已結束的 runs + 對應工作目錄
- Query（擇一提供 cutoff）：
  - `before=YYYY-MM-DD`（指定日期 00:00 之前）
  - `older_than_days=int`（>0：早於 N 天；<=0：不套時間條件，表示清所有已結束）
- 其他 Query：
  - `status`（可選）：例如 `passed`
  - `dry_run=1`（可選）：只預估不刪
- 回應：
  - dry-run：`{"ok": true, "would_delete": <n>, "ids": [..]}`
  - real：`{"ok": true, "deleted": <n>, "ids": [..]}`

### curl
清理所有已 finished 的 runs（最常用）：
```bash
curl -sS -X DELETE "$CHARTER_BASE/api/runs/purge?older_than_days=0" | jq .
```

只試算不刪：
```bash
curl -sS -X DELETE "$CHARTER_BASE/api/runs/purge?older_than_days=0&dry_run=1" | jq .
```

## GET `/api/runs/worker/status`
- 用途：簡易 worker status（queued/running 計數）
- 回應：`{"idle": true|false, "queue": <queued_count>}`

### curl
```bash
curl -sS "$CHARTER_BASE/api/runs/worker/status" | jq .
```

## GET `/api/runs/{run_id}/log-archives`
- 用途：列出失敗 run 的 cpe_log 壓縮檔（*.tar.gz/*.tgz）

### curl
```bash
RID=1234
curl -sS "$CHARTER_BASE/api/runs/$RID/log-archives" | jq .
```

### 回應（範例）
```json
[{"name":"...tar.gz","size":123,"mtime":<fill>0}, ...]
```

## GET `/api/runs/{run_id}/log-archive?name=...`
- 用途：下載指定或最新的 log archive
- Query：
  - `name`（可選）：不給則下載最新
- 回應：`application/gzip`（FileResponse）

### curl
下載最新：
```bash
RID=1234
curl -fsSL "$CHARTER_BASE/api/runs/$RID/log-archive" -o run_${RID}_cpe_log.tar.gz
```

指定檔名下載：
```bash
RID=1234
NAME='90d3cf...-logpull-20260224-124020.tar.gz'
curl -fsSL "$CHARTER_BASE/api/runs/$RID/log-archive?name=$NAME" -o "$NAME"
```
