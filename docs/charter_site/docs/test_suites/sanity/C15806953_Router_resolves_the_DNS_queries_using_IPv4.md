# C15806953_Router_resolves_the_DNS_queries_using_IPv4

DNS 查詢測試（IPv4）

---

## 腳本說明

- **功能**：驗證路由器可正確解析 DNS 查詢
- **版本**：v1
- **Entrypoint**：`cycle_wrapper.py:run`

---

## 執行資訊

| 項目 | 值 |
|------|-----|
| Suite | sanity |
| Script ID（11F_140） | 5231 |

---

## 參數分組

### 執行控制

| 參數 | 值 | 說明 |
|------|-----|------|
| `CYCLES` | 1 | 迴圈次數 |
| `STOP_ON_FAIL` | 1 | 失敗停止 |

### DNS 設定

| 參數 | 值 | 說明 |
|------|-----|------|
| `TARGET` | www.google.com | DNS 目標 |
| `ENABLE_DNS_CHECK` | 1 | 啟用 DNS 檢查 |

---

## Run（API）

```bash
SCRIPT_ID=5231
curl -sS -X POST "$CHARTER_BASE/api/scripts/$SCRIPT_ID/run" | python3 -m json.tool
```

---

## 看結果

```bash
RID=<RUN_ID>
curl -fsSL "$CHARTER_BASE/api/runs/$RID/log" > run_${RID}_log.json
```

---

## Cleanup

```bash
curl -sS -X DELETE "$CHARTER_BASE/api/runs/purge?older_than_days=0"
```

---

## 下載腳本

```bash
SCRIPT_ID=5231
curl -fsSL "$CHARTER_BASE/api/scripts/$SCRIPT_ID/export" -o "C15806953_$SCRIPT_ID.zip"
```
