# C15807240_Warehouse_Web_Page_should_load_with_IPv4_address_on_LAN

Warehouse IPv4 測試

---

## 腳本說明

- **功能**：驗證 LAN Client 可用 IPv4 載入 Warehouse 網頁
- **版本**：v1
- **Entrypoint**：`cycle_wrapper.py:run`

---

## 執行資訊

| 項目 | 值 |
|------|-----|
| Suite | sanity |
| Script ID（11F_140） | 5243 |

---

## 參數分組

### 執行控制

| 參數 | 值 | 說明 |
|------|-----|------|
| `CYCLES` | 1 | 迴圈次數 |

---

## Run（API）

```bash
SCRIPT_ID=5243
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
SCRIPT_ID=5243
curl -fsSL "$CHARTER_BASE/api/scripts/$SCRIPT_ID/export" -o "C15807240_$SCRIPT_ID.zip"
```
