# Scripts

對應 UI：`/scripts`、`/suites`

## GET `/api/scripts`
- 用途：列出腳本
- Query:
  - `suite`（可選）：`stability|sanity|regression`（`all` 或空值代表不過濾）
  - `q`（可選）：名稱關鍵字（ILIKE %q%）

### curl
列出所有 scripts：
```bash
curl -sS "$CHARTER_BASE/api/scripts" | jq .
```

只列 sanity：
```bash
curl -sS "$CHARTER_BASE/api/scripts?suite=sanity" | jq .
```

搜尋名稱關鍵字：
```bash
curl -sS "$CHARTER_BASE/api/scripts?suite=sanity&q=DHCP" | jq .
```

### 回應
`Script[]`
- `id: number`
- `name: string`
- `suite: string`
- `entrypoint: string`（例：`main.py:run`）
- `created_at/updated_at: string|null`（依 DB / 序列化情形）
- `zip_path: string|null`

## POST `/api/scripts/import2`
- 用途：匯入腳本（新版；前端 Suites 頁優先使用）
- Content-Type：`multipart/form-data`
- Form:
  - `suite`：`stability|sanity|regression`
  - `file`：`.zip`

### curl
匯入單一 zip：
```bash
curl -sS -X POST "$CHARTER_BASE/api/scripts/import2" \
  -F 'suite=sanity' \
  -F 'file=@./your_script.zip;type=application/zip' | jq .
```

### 行為
- 支援「單一 zip」或「大包 zip 內含多個 *.zip」
- 子 zip 會做檢查（預設強制需要）：`main.py`、`manifest.yaml`、`requirements.txt`
- `manifest.yaml` 可提供 `name`、`entry`
- 若同 suite 下 `name` 已存在 → `skipped/DUPLICATE`

### 回應（範例）
```json
{
  "ok": true,
  "stats": {"total": 0, "created": 0, "skipped": 0, "failed": 0},
  "results": [
    {"name": "...", "action": "created", "id": 123},
    {"name": "...", "action": "skipped", "reason": "DUPLICATE"},
    {"name": "...", "action": "failed", "reason": "MISSING_FILES", "missing": ["..."]}
  ]
}
```

### 常見錯誤/注意
- `skipped/DUPLICATE`：同 suite+name 已存在（DA40 規範：**先刪同名再匯入**）
- `failed/MISSING_FILES`：zip 內容缺 `main.py`/`manifest.yaml`/`requirements.txt`

## POST `/api/scripts/import`
- 用途：匯入腳本（舊版；import2 失敗時前端 fallback）
- Content-Type：`multipart/form-data`
- Form:
  - `suite`：`stability|sanity|regression`
  - `file`：`.zip`

### curl
```bash
curl -sS -X POST "$CHARTER_BASE/api/scripts/import" \
  -F 'suite=sanity' \
  -F 'file=@./your_script.zip;type=application/zip' | jq .
```

### 行為
- 支援「單一 zip」或「大包 zip 內含多個 *.zip」
- 若 manifest 存在：讀 `manifest.yaml` 的 `name`，以及 `entry`/`entrypoint`
- DB unique 衝突時會自動幫 name 加 suffix 重試（最多 9 次）

### 回應（範例）
```json
{"ok": true, "created": [{"id":1,"name":"..."}], "errors": []}
```

### 注意
- 因為會自動改名避免衝突，**不符合「同名先刪再匯入」的治理需求**；建議優先用 `/import2`。

## POST `/api/scripts/{script_id}/run`
- 用途：執行某腳本（建立一筆 run，狀態 queued）

### curl
```bash
SCRIPT_ID=123
curl -sS -X POST "$CHARTER_BASE/api/scripts/$SCRIPT_ID/run" | jq .
```

### 回應
- 成功：`{"ok": true, "run_id": <rid>}`
- 404：`{"ok": false, "error": "script not found"}`

### 常見錯誤/注意
- 若 worker 忙碌：run 可能 queued 一段時間（用 `GET /api/runs/worker/status` 看 queue）。

## DELETE `/api/scripts/{script_id}`
- 用途：刪除 script + 其 runs；並嘗試刪除磁碟 zip 與對應 venv

### curl
```bash
SCRIPT_ID=123
curl -sS -X DELETE "$CHARTER_BASE/api/scripts/$SCRIPT_ID" | jq .
```

### 回應（範例）
```json
{
  "ok": true,
  "file_deleted": true,
  "venv_deleted": true,
  "file_path": "...",
  "venv_path": "..."
}
```

### 注意
- 此操作具破壞性（會刪 script 與相關 runs/venv），建議先 export 備份。

## GET `/api/scripts/{script_id}/export`
- 用途：下載腳本 zip
- 回應：`application/zip`（StreamingResponse）
- Headers：`Content-Disposition: attachment; filename="<...>.zip"`

### curl
```bash
SCRIPT_ID=123
curl -fsSL "$CHARTER_BASE/api/scripts/$SCRIPT_ID/export" -o script_${SCRIPT_ID}.zip
```

## GET `/api/scripts/{script_id}/manifest`
- 用途：讀取 manifest.yaml / manifest.yml
- 特性：GET 允許在 DB 的 zip_path 不準時做 fallback（協助維運查看）

### curl
```bash
SCRIPT_ID=123
curl -sS "$CHARTER_BASE/api/scripts/$SCRIPT_ID/manifest" | jq .
```

### 回應
```json
{"ok": true, "content": "...yaml...", "zip_used": "...", "fallback_used": false}
```

## PUT `/api/scripts/{script_id}/manifest`
- 用途：更新 manifest（會把 zip 重新打包覆寫 manifest 檔）

### curl
```bash
SCRIPT_ID=123
jq -n --arg content "$(cat manifest.yaml)" '{content:$content}' \
  | curl -sS -X PUT "$CHARTER_BASE/api/scripts/$SCRIPT_ID/manifest" \
      -H 'Content-Type: application/json' \
      -d @- | jq .
```

### Body
```json
{"content": "<manifest yaml text>"}
```

### 回應
```json
{"ok": true, "updated_entrypoint": "main.py:run", "zip_used": "..."}
```

### 常見錯誤/注意
- 若更新後 entrypoint/requirements 不一致，run 時可能在 worker 端報錯（pip/install 或 entry resolve）。
