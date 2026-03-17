# C00000004_NOC_API_basic_test

NOC API 基本測試

---

## 腳本說明

- **功能**：驗證 NOC API 連線與基本功能
- **版本**：v3-professional-noc_profile-only-nodeid-cpeinfo
- **Entrypoint**：`cycle_wrapper.py:run`

---

## 執行資訊

| 項目 | 值 |
|------|-----|
| Suite | sanity |
| Script ID（11F_140） | 5228 |
| 版本 | v3-professional-noc_profile-only-nodeid-cpeinfo |
| Entrypoint | cycle_wrapper.py:run |

---

## 參數分組

### 執行控制

| 參數 | 值 | 說明 |
|------|-----|------|
| `CYCLES` | 1 | 迴圈次數 |
| `CYCLE_INTERVAL` | 70 | 迴圈間隔（秒） |
| `STOP_ON_FAIL` | 1 | 失敗停止 |

### NOC API

| 參數 | 值 | 說明 |
|------|-----|------|
| `NOC_BASE` | https://piranha-int.tau.dev-charter.net | NOC 端點 |
| `PROFILES_FILE` | /home/da40/charter/.secrets/noc_profiles.json | 帳號檔 |
| `NOC_PROFILE` | SPECTRUM_INT | Profile 名稱 |
| `CUSTOMER_ID` | 682d4e5179b80027cd6fb27e | 客戶 ID |
| `ENABLE_NOC_API_TESTS` | 1 | 啟用 NOC API 測試 |

---

## Run（API）

```bash
export CHARTER_BASE="http://172.14.1.140:5173"
SCRIPT_ID=5228

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
SCRIPT_ID=5228
curl -fsSL "$CHARTER_BASE/api/scripts/$SCRIPT_ID/export" -o "C00000004_NOC_API_basic_test_$SCRIPT_ID.zip"
```

---

## GitHub

- [scripts/sanity/C00000004_NOC_API_basic_test.zip](https://github.com/askeywifisit-ui/charter_project/tree/main/scripts/sanity)
