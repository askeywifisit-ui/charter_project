# C15807173_Test_Upnp_discovery

> ⚠️ 此 Repo 為 Private，需登入 GitHub 才能下載。

UPnP 探索測試

---

## 腳本說明

- **功能**：驗證 UPnP 探索與狀態變更
- **版本**：v1
- **Entrypoint**：`cycle_wrapper.py:run`

---

## 執行資訊

| 項目 | 值 |
|------|-----|
| Suite | sanity |
| Script ID（11F_140） | 5242 |

---

## 參數分組

### 執行控制

| 參數 | 值 | 說明 |
|------|-----|------|
| `CYCLES` | 1 | 迴圈次數 |
| `STOP_ON_FAIL` | 1 | 失敗停止 |

### NOC API

| 參數 | 值 | 說明 |
|------|-----|------|
| `NOC_PROFILE` | SPECTRUM_INT | Profile 名稱 |
| `CUSTOMER_ID` | 682d4e5179b80027cd6fb27e | 客戶 ID |

---

## Run（API）

```bash
SCRIPT_ID=5242
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
SCRIPT_ID=5242
curl -fsSL "$CHARTER_BASE/api/scripts/$SCRIPT_ID/export" -o "C15807173_Test_Upnp_discovery_$SCRIPT_ID.zip"
```

---

## GitHub

- [scripts/sanity/C15807173_Test_Upnp_discovery.zip](https://github.com/askeywifisit-ui/charter_project/tree/main/scripts/sanity)
