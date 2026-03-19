# Runs API

對應 UI：`/runs`

---

## GET /api/runs

列出執行記錄

### Request

```bash
curl -sS "http://172.14.1.140:5173/api/runs?limit=50" | jq .
```

### Query Parameters

| 參數 | 說明 | 範例 |
|------|------|------|
| `limit` | 數量限制 | `50`, `100` |
| `status` | 狀態過濾 | `passed`, `failed`, `running` |

### Response

```json
[
  {
    "id": 7500,
    "script_id": 5225,
    "status": "passed",
    "started_at": "2026-03-17T10:30:00Z",
    "finished_at": "2026-03-17T10:35:00Z"
  }
]
```

---

## GET /api/runs/{id}

查看執行結果

### Request

```bash
curl -sS "http://172.14.1.140:5173/api/runs/7500" | jq .
```

### Response

```json
{
  "id": 7500,
  "script_id": 5225,
  "status": "passed",
  "exit_code": 0,
  "started_at": "2026-03-17T10:30:00Z",
  "finished_at": "2026-03-17T10:35:00Z"
}
```

---

## GET /api/runs/{id}/log

下載執行日誌

### Request

```bash
curl -sS "http://172.14.1.140:5173/api/runs/7500/log" -o run_7500_log.json
```

---

## DELETE /api/runs/purge

清理舊執行記錄

### Request

```bash
# 清理所有已完成的 runs
curl -sS -X DELETE "http://172.14.1.140:5173/api/runs/purge?older_than_days=0" | jq .

# 清理 7 天前的
curl -sS -X DELETE "http://172.14.1.140:5173/api/runs/purge?older_than_days=7" | jq .
```

### Response

```json
{
  "ok": true,
  "deleted_runs": 50
}
```

---

## GET /api/runs/worker/status

Worker 狀態

### Request

```bash
curl -sS "http://172.14.1.140:5173/api/runs/worker/status" | jq .
```

### Response

```json
{
  "status": "idle"
}
```

或

```json
{
  "status": "running",
  "current_run_id": 7500
}
```

---

## 相關頁面

- [Scripts API](/api_reference/scripts/)
- [Worker API](/api_reference/worker/)
