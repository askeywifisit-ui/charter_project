# C15807241_Warehouse_Web_Page_should_load_with_IPv6_Link_Local_address_on_LAN

> ⚠️ 此 Repo 為 Private，需登入 GitHub 才能下載。

Warehouse IPv6 測試

---

## 腳本說明

- **功能**：驗證 LAN Client 可用 IPv6 Link-Local 載入 Warehouse 網頁
- **版本**：v1
- **Entrypoint**：`cycle_wrapper.py:run`

---

## 執行資訊

| 項目 | 值 |
|------|-----|
| Suite | sanity |
| Script ID（11F_140） | 5255 |

---

## 參數分組

### 執行控制

| 參數 | 值 | 說明 |
|------|-----|------|
| `CYCLES` | 1 | 迴圈次數 |

---

## Run（API）

```bash
SCRIPT_ID=5255
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
SCRIPT_ID=5255
curl -fsSL "$CHARTER_BASE/api/scripts/$SCRIPT_ID/export" -o "C15807241_$SCRIPT_ID.zip"
```
