# Health / 基礎

## GET `/api/health`
- 用途：健康檢查

### curl
```bash
curl -sS "$CHARTER_BASE/api/health"
```

### 回應
- main.py 版本：
  - `{"ok": true}`
- work.py 版本：
  - `{"ok": true, "time": "<iso>"}`

### 常見錯誤/注意
- 同一路徑在不同模組都有定義，實際以掛載順序生效（目前 main.py 有 include work.py 的 router，也有自己定義）。
