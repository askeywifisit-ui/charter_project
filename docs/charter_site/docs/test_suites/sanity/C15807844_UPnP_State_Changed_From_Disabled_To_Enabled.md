# C15807844_UPnP_State_Changed_From_Disabled_To_Enabled

> ⚠️ 此 Repo 為 Private，需登入 GitHub 才能下載。

UPnP 開測試

---

## 腳本說明

- **功能**：驗證 UPnP 從關閉變為開啟
- **版本**：v1
- **Entrypoint**：`cycle_wrapper.py:run`

---

## 執行資訊

| 項目 | 值 |
|------|-----|
| Suite | sanity |
| Script ID（11F_140） | 5246 |

---

## 參數分組

### 執行控制

| 參數 | 值 | 說明 |
|------|-----|------|
| `CYCLES` | 1 | 迴圈次數 |

---

## Run（API）

```bash
SCRIPT_ID=5246
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
SCRIPT_ID=5246
curl -fsSL "$CHARTER_BASE/api/scripts/$SCRIPT_ID/export" -o "C15807844_$SCRIPT_ID.zip"
```
