# C00000001_SSH_basic_test

SSH 行為/權限驗證（allow/deny/port/session/credential 等）

---

## 腳本說明

- **功能**：驗證 SSH 允許/拒絕/連接數/credential 等行為
- **版本**：v3-professional-noc_profile-only-nodeid-cpeinfo
- **Entrypoint**：`cycle_wrapper.py:run`

---

## 執行資訊

| 項目 | 值 |
|------|-----|
| Suite | sanity |
| Script ID（11F_140） | 5162 |
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
| `CPE_SSH_TOOL` | /home/da40/charter/tools/cpe_ssh.py | SSH 工具 |

### CPE 連線

| 參數 | 值 | 說明 |
|------|-----|------|
| `CPE_BAUD` | 115200 | Serial 鮑率 |
| `CPE_USER` | root | CPE 帳號 |
| `CPE_PASSWORD` | null | CPE 密碼 |
| `CPE_READY_CHECK` | 1 | 檢查 CPE 就緒 |
| `CPE_INFO_STATUS_CMD` | cpe_info --status | 狀態指令 |

### SSH 設定

| 參數 | 值 | 說明 |
|------|-----|------|
| `SSH_USER` | operator | SSH 帳號 |
| `SSH_PASSWORD` | \<fill\> | SSH 密碼 |
| `SSH_TIMEOUT_MIN` | 120 | SSH 逾時（分） |
| `SSH_HOST_LAN` | 192.168.1.1 | LAN IP |
| `WAN_SSH_REQUIRED` | 1 | 需要 WAN SSH |
| `LAN_SSH_REQUIRED` | 1 | 需要 LAN SSH |
| `SSH_TOOL_TIMEOUT` | 15 | 工具逾時 |
| `USE_CLOUD_SSH` | 1 | 使用 Cloud SSH |

### NOC API

| 參數 | 值 | 說明 |
|------|-----|------|
| `NOC_BASE` | https://piranha-int.tau.dev-charter.net | NOC 端點 |
| `PROFILES_FILE` | /home/da40/charter/.secrets/noc_profiles.json | 帳號檔 |
| `NOC_PROFILE` | SPECTRUM_INT | Profile 名稱 |
| `CUSTOMER_ID` | 682d4e5179b80027cd6fb27e | 客戶 ID |
| `ENABLE_NOC_API_TESTS` | 0 | 啟用 NOC API 測試 |

### Reboot 設定

| 參數 | 值 | 說明 |
|------|-----|------|
| `ENABLE_REBOOT_TEST` | 0 | 啟用重啟測試 |
| `REBOOT_DELAY_SEC` | 2 | 重啟延遲 |
| `REBOOT_MUTE_SECS` | 60 | 靜音秒數 |
| `REBOOT_MUTE_WITH_LOCK` | 0 | 靜音加鎖 |

### PDU 設定

| 參數 | 值 | 說明 |
|------|-----|------|
| `PDU_RESET_ON_NOT_READY` | 1 | 未就緒時重置 |
| `PDU_RESET_ACTION` | reset | 重置動作 |
| `PDU_RESET_TIMEOUT_SEC` | 120 | 重置逾時 |
| `PDU_RESET_WAIT_SEC` | 120 | 重置等待 |

### 網路檢查

| 參數 | 值 | 說明 |
|------|-----|------|
| `INTERNET_CHECK_MAX_RETRIES` | 10 | 網路檢查重試次數 |
| `INTERNET_CHECK_INTERVAL_SEC` | 3 | 檢查間隔 |
| `ENABLE_DNS_CHECK` | 0 | 啟用 DNS 檢查 |

---

## Run（API）

```bash
export CHARTER_BASE="http://172.14.1.140:5173"
SCRIPT_ID=5162

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

# 下載 CPE logs
curl -fsSL "$CHARTER_BASE/api/runs/$RID/log-archive" -o run_${RID}_cpe_log.tar.gz
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
SCRIPT_ID=5162

mkdir -p backup
curl -fsSL "$CHARTER_BASE/api/scripts/$SCRIPT_ID/export" -o "backup/C00000001_SSH_basic_test_${SCRIPT_ID}.zip"
```

---

## GitHub

- [scripts/sanity/C00000001_SSH_basic_test.zip](https://github.com/askeywifisit-ui/charter_project/tree/main/scripts/sanity)
