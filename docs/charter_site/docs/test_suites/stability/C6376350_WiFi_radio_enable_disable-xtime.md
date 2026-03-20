# C6376350_WiFi_radio_enable_disable-xtime

> ⚠️ 此 Repo 為 Private，需登入 GitHub 才能下載。

WiFi Radio 開關長跑（Stability）

---

## 腳本說明

- **功能**：WiFi Radio 開關多次長跑測試
- **版本**：v1
- **Entrypoint**：`cycle_wrapper.py:run`

---

## 執行資訊

| 項目 | 值 |
|------|-----|
| Suite | stability |
| Script ID（11F_140） | 5123 |

---

## 參數分組

### 執行控制

| 參數 | 值 | 說明 |
|------|-----|------|
| `CYCLES` | 10 | 迴圈次數 |

---

## Run（API）

```bash
SCRIPT_ID=5123
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
SCRIPT_ID=5123
curl -fsSL "$CHARTER_BASE/api/scripts/$SCRIPT_ID/export" -o "C6376350_$SCRIPT_ID.zip"
```
