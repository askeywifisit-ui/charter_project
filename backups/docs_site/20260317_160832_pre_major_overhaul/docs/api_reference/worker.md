# Worker

## GET `/api/worker`
## GET `/api/worker/state`
- 用途：前端 Runs 頁顯示 Worker idle/busy 與 queue
- 回應：`{"idle": true|false, "queue": <queued_count>}`

### curl
```bash
curl -sS "$CHARTER_BASE/api/worker" | jq .
curl -sS "$CHARTER_BASE/api/worker/state" | jq .
```

> 補充：runs 也有一個簡易狀態端點：`GET /api/runs/worker/status`
