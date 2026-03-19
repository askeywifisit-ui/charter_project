# Scripts API

對應 UI：`/scripts`、`/suites`

---

## GET /api/scripts

列出腳本

### Request

```bash
curl -sS "http://172.14.1.140:5173/api/scripts?limit=100" | jq .
```

### Query Parameters

| 參數 | 說明 | 範例 |
|------|------|------|
| `suite` | 過濾 suite | `sanity`, `stability`, `regression` |
| `q` | 名稱關鍵字 | `DHCP`, `SSH` |
| `limit` | 數量限制 | `100`, `2000` |

### Response

```json
[
  {
    "id": 5225,
    "name": "C00000001_SSH_basic_test",
    "suite": "sanity",
    "entrypoint": "cycle_wrapper.py:run",
    "created_at": "2026-01-15T10:30:00Z",
    "zip_path": "/data/scripts/upload_xxx.zip"
  }
]
```

---

## POST /api/scripts/import2

匯入腳本

### Request

```bash
curl -sS -X POST "http://172.14.1.140:5173/api/scripts/import2" \
  -F "suite=sanity" \
  -F "file=@./my_script.zip;type=application/zip" | jq .
```

### Response

成功：
```json
{
  "ok": true,
  "id": 5300,
  "name": "C00000001_SSH_basic_test"
}
```

失敗：
```json
{
  "ok": false,
  "reason": "MISSING_FILES",
  "missing": ["requirements.txt"]
}
```

---

## GET /api/scripts/{id}/export

匯出腳本

### Request

```bash
curl -sS "http://172.14.1.140:5173/api/scripts/5225/export" -o backup.zip
```

---

## DELETE /api/scripts/{id}

刪除腳本

### Request

```bash
curl -sS -X DELETE "http://172.14.1.140:5173/api/scripts/5225" | jq .
```

### Response

```json
{
  "ok": true
}
```

---

## POST /api/scripts/{id}/run

執行腳本

### Request

```bash
curl -sS -X POST "http://172.14.1.140:5173/api/scripts/5225/run" | jq .
```

### Response

```json
{
  "run_id": 7500
}
```

---

## 相關頁面

- [Runs API](/api_reference/runs/)
- [Worker API](/api_reference/worker/)
- [Health API](/api_reference/health/)
