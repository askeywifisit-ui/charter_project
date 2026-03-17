# A2435635_Continuously_executing_speedtest

持續 Speedtest（Stability）

---

## 腳本說明

- **功能**：長時間持續執行 Speedtest
- **版本**：v1
- **Entrypoint**：`cycle_wrapper.py:run`

---

## 執行資訊

| 項目 | 值 |
|------|-----|
| Suite | stability |
| Script ID（11F_140） | 5224 |

---

## 參數分組

### 執行控制

| 參數 | 值 | 說明 |
|------|-----|------|
| `CYCLES` | 10 | 迴圈次數 |
| `CYCLE_INTERVAL` | 120 | 間隔秒數 |

---

## Run（API）

```bash
SCRIPT_ID=5224
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
SCRIPT_ID=5224
curl -fsSL "$CHARTER_BASE/api/scripts/$SCRIPT_ID/export" -o "A2435635_$SCRIPT_ID.zip"
```
