# C15807130_SSH_allowed_local_IP_from_WLAN_Client

SSH WLAN Client 測試

---

## 腳本說明

- **功能**：驗證 WLAN Client 可用本地 IP SSH
- **版本**：v1
- **Entrypoint**：`cycle_wrapper.py:run`

---

## 執行資訊

| 項目 | 值 |
|------|-----|
| Suite | sanity |
| Script ID（11F_140） | 5253 |

---

## 參數分組

### 執行控制

| 參數 | 值 | 說明 |
|------|-----|------|
| `CYCLES` | 1 | 迴圈次數 |
| `STOP_ON_FAIL` | 1 | 失敗停止 |

### WiFi 設定

| 參數 | 值 | 說明 |
|------|-----|------|
| `WIFI_IFACE` | \<fill\> | WiFi 介面 |

---

## Run（API）

```bash
SCRIPT_ID=5253
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
SCRIPT_ID=5253
curl -fsSL "$CHARTER_BASE/api/scripts/$SCRIPT_ID/export" -o "C15807130_$SCRIPT_ID.zip"
```
