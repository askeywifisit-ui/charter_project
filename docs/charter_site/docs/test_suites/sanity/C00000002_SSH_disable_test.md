# C00000002_SSH_disable_test

SSH 關閉測試

---

## 腳本說明

- **功能**：驗證 SSH 關閉功能
- **版本**：v3-professional-noc_profile-only-nodeid-cpeinfo
- **Entrypoint**：`cycle_wrapper.py:run`

---

## 執行資訊

| 項目 | 值 |
|------|-----|
| Suite | sanity |
| Script ID（11F_140） | 5226 |
| 版本 | v3-professional-noc_profile-only-nodeid-cpeinfo |
| Entrypoint | cycle_wrapper.py:run |

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
| `SSH_USER` | operator | SSH 帳號 |
| `SSH_PASSWORD` | \<fill\> | SSH 密碼 |
| `SSH_ACTION` | disable | SSH 動作 |

### NOC API

| 參數 | 值 | 說明 |
|------|-----|------|
| `NOC_PROFILE` | SPECTRUM_INT | Profile 名稱 |
| `CUSTOMER_ID` | 682d4e5179b80027cd6fb27e | 客戶 ID |

---

## Run（API）

```bash
export CHARTER_BASE="http://172.14.1.140:5173"
SCRIPT_ID=5226

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
SCRIPT_ID=5226
curl -fsSL "$CHARTER_BASE/api/scripts/$SCRIPT_ID/export" -o "C00000002_SSH_disable_test_$SCRIPT_ID.zip"
```

---

## GitHub

- [scripts/sanity/C00000002_SSH_disable_test.zip](https://github.com/askeywifisit-ui/charter_project/tree/main/scripts/sanity)
