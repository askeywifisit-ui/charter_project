# C4123492_IPv4_Stability_Test_from_LAN_Client

IPv4 穩定性測試（Stability）

---

## 腳本說明

- **功能**：從 LAN Client 進行 IPv4 穩定性測試
- **版本**：v1
- **Entrypoint**：`cycle_wrapper.py:run`

---

## 執行資訊

| 項目 | 值 |
|------|-----|
| Suite | stability |
| Script ID（11F_140） | 5121 |

---

## 參數分組

### 執行控制

| 參數 | 值 | 說明 |
|------|-----|------|
| `CYCLES` | 10 | 迴圈次數 |

---

## Run（API）

```bash
SCRIPT_ID=5121
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
SCRIPT_ID=5121
curl -fsSL "$CHARTER_BASE/api/scripts/$SCRIPT_ID/export" -o "C4123492_$SCRIPT_ID.zip"
```
