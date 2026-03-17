# A2844344_Continuously_executing_reboot

持續重啟測試（Stability）

---

## 腳本說明

- **功能**：長時間持續執行 reboot 測試
- **版本**：v1
- **Entrypoint**：`cycle_wrapper.py:run`

---

## 執行資訊

| 項目 | 值 |
|------|-----|
| Suite | stability |
| Script ID（11F_140） | 5116 |

---

## 參數分組

### 執行控制

| 參數 | 值 | 說明 |
|------|-----|------|
| `CYCLES` | 10 | 迴圈次數（預設） |
| `CYCLE_INTERVAL` | 120 | 迴圈間隔（秒） |
| `STOP_ON_FAIL` | 1 | 失敗停止 |

### Reboot 設定

| 參數 | 值 | 說明 |
|------|-----|------|
| `REBOOT_MUTE_SECS` | 120 | 靜音秒數 |
| `ENABLE_REBOOT_TEST` | 1 | 啟用重啟測試 |

### NOC API

| 參數 | 值 | 說明 |
|------|-----|------|
| `NOC_PROFILE` | SPECTRUM_INT | Profile 名稱 |
| `CUSTOMER_ID` | 682d4e5179b80027cd6fb27e | 客戶 ID |

---

## Run（API）

```bash
SCRIPT_ID=5116

# 建議先調整 CYCLES（長跑）
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
SCRIPT_ID=5116
curl -fsSL "$CHARTER_BASE/api/scripts/$SCRIPT_ID/export" -o "A2844344_Continuously_executing_reboot_$SCRIPT_ID.zip"
```

---

## GitHub

- [scripts/stability/A2844344_Continuously_executing_reboot.zip](https://github.com/askeywifisit-ui/charter_project/tree/main/scripts/stability)
