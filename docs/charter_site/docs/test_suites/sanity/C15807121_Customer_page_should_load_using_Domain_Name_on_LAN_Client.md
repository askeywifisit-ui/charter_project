# C15807121_Customer_page_should_load_using_Domain_Name_on_LAN_Client

> ⚠️ 此 Repo 為 Private，需登入 GitHub 才能下載。

Customer Page 網域測試

---

## 腳本說明

- **功能**：驗證 LAN Client 可透過網域載入 Customer 頁面
- **版本**：v1
- **Entrypoint**：`cycle_wrapper.py:run`

---

## 執行資訊

| 項目 | 值 |
|------|-----|
| Suite | sanity |
| Script ID（11F_140） | 5234 |

---

## 參數分組

### 執行控制

| 參數 | 值 | 說明 |
|------|-----|------|
| `CYCLES` | 1 | 迴圈次數 |
| `STOP_ON_FAIL` | 1 | 失敗停止 |

---

## Run（API）

```bash
SCRIPT_ID=5234
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
SCRIPT_ID=5234
curl -fsSL "$CHARTER_BASE/api/scripts/$SCRIPT_ID/export" -o "C15807121_$SCRIPT_ID.zip"
```
