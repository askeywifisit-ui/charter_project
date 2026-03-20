# C00000003_WIFI_basic_test

> ⚠️ 此 Repo 為 Private，需登入 GitHub 才能下載。

WiFi 基本連線測試

---

## 腳本說明

- **功能**：驗證 WiFi 基本連線功能
- **版本**：v3-professional-noc_profile-only-nodeid-cpeinfo
- **Entrypoint**：`cycle_wrapper.py:run`

---

## 執行資訊

| 項目 | 值 |
|------|-----|
| Suite | sanity |
| Script ID（11F_140） | 5227 |
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
| `ENABLE_HEALTH_WARNING` | 1 | 啟用健康警告 |

### 工具路徑

| 參數 | 值 | 說明 |
|------|-----|------|
| `TOOLS_PATH` | /home/da40/charter/tools | 工具目錄 |
| `CPE_INFO_TOOL` | /home/da40/charter/tools/cpe_info | CPE 資訊工具 |
| `WIFI_IWD_TOOL` | /home/da40/charter/tools/wifi_iwd.py | WiFi 工具 |

### WiFi 設定

| 參數 | 值 | 說明 |
|------|-----|------|
| `WIFI_IFACE` | \<fill\> | WiFi 介面 |
| `WIFI_SSID` | \<fill\> | SSID |
| `WIFI_PASSWORD` | \<fill\> | 密碼 |
| `WIFI_BAND` | auto | 頻段 |

### NOC API

| 參數 | 值 | 說明 |
|------|-----|------|
| `NOC_BASE` | https://piranha-int.tau.dev-charter.net | NOC 端點 |
| `PROFILES_FILE` | /home/da40/charter/.secrets/noc_profiles.json | 帳號檔 |
| `NOC_PROFILE` | SPECTRUM_INT | Profile 名稱 |
| `CUSTOMER_ID` | 682d4e5179b80027cd6fb27e | 客戶 ID |

---

## Run（API）

```bash
export CHARTER_BASE="http://172.14.1.140:5173"
SCRIPT_ID=5227

# 確認 worker 正常
curl -fsSL "$CHARTER_BASE/api/runs/worker/status" | python3 -m json.tool

# 送出 run
curl -sS -X POST "$CHARTER_BASE/api/scripts/$SCRIPT_ID/run" | python3 -m json.tool
```

---

## 看結果

```bash
RID=<RUN_ID>

# 查看狀態
curl -fsSL "$CHARTER_BASE/api/runs/$RID"

# 查看 log
curl -fsSL "$CHARTER_BASE/api/runs/$RID/log" > run_${RID}_log.json
```

---

## Cleanup

```bash
# 清理 runs + workdir
curl -sS -X DELETE "$CHARTER_BASE/api/runs/purge?older_than_days=0" | python3 -m json.tool
```

---

## 下載腳本

```bash
export CHARTER_BASE="http://172.14.1.140:5173"
SCRIPT_ID=5227

mkdir -p backup
curl -fsSL "$CHARTER_BASE/api/scripts/$SCRIPT_ID/export" -o "backup/C00000003_WIFI_basic_test_${SCRIPT_ID}.zip"
```

---

## GitHub

- [scripts/sanity/C00000003_WIFI_basic_test.zip](https://github.com/askeywifisit-ui/charter_project/tree/main/scripts/sanity)
