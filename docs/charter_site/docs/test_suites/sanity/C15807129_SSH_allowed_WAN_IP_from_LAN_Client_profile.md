# C15807129_SSH_allowed_WAN_IP_from_LAN_Client_profile

> ⚠️ 此 Repo 為 Private，需登入 GitHub 才能下載。

SSH WAN IP 測試

---

## 腳本說明

- **功能**：驗證可從 LAN Client profile 使用 WAN IP SSH
- **版本**：v1
- **Entrypoint**：`cycle_wrapper.py:run`

---

## 執行資訊

| 項目 | 值 |
|------|-----|
| Suite | sanity |
| Script ID（11F_140） | 5236 |

---

## 參數分組

### 執行控制

| 參數 | 值 | 說明 |
|------|-----|------|
| `CYCLES` | 1 | 迴圈次數 |
| `STOP_ON_FAIL` | 1 | 失敗停止 |

### SSH 設定

| 參數 | 值 | 說明 |
|------|-----|------|
| `WAN_SSH_REQUIRED` | 1 | 需要 WAN SSH |

---

## Run（API）

```bash
SCRIPT_ID=5236
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
SCRIPT_ID=5236
curl -fsSL "$CHARTER_BASE/api/scripts/$SCRIPT_ID/export" -o "C15807129_$SCRIPT_ID.zip"
```
