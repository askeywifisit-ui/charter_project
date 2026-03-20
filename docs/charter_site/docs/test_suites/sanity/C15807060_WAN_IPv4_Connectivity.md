# C15807060_WAN_IPv4_Connectivity

> ⚠️ 此 Repo 為 Private，需登入 GitHub 才能下載。

WAN IPv4 連線測試

---

## 腳本說明

- **功能**：驗證 WAN IPv4 連線功能
- **版本**：v1
- **Entrypoint**：`cycle_wrapper.py:run`

---

## 執行資訊

| 項目 | 值 |
|------|-----|
| Suite | sanity |
| Script ID（11F_140） | 5232 |

---

## 參數分組

### 執行控制

| 參數 | 值 | 說明 |
|------|-----|------|
| `CYCLES` | 1 | 迴圈次數 |
| `STOP_ON_FAIL` | 1 | 失敗停止 |

### 網路檢查

| 參數 | 值 | 說明 |
|------|-----|------|
| `INTERNET_CHECK_MAX_RETRIES` | 10 | 重試次數 |
| `INTERNET_CHECK_INTERVAL_SEC` | 3 | 檢查間隔 |

---

## Run（API）

```bash
SCRIPT_ID=5232
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
SCRIPT_ID=5232
curl -fsSL "$CHARTER_BASE/api/scripts/$SCRIPT_ID/export" -o "C15807060_$SCRIPT_ID.zip"
```
