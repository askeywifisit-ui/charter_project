# A2844344_Continuously_executing_reboot

- Suite: **stability**
- Script ID（可能因 delete/import 變動）：`11F_140=5116`
- 版本（manifest version）：`v2-professional-noc_profile-only-nodeid-cpeinfo`
- Entrypoint：`cycle_wrapper.py:run`

> 本頁由工具依 11F_140 最新 export zip 自動產生/更新（2026-03-10）。

## 目的（Purpose）

（以腳本內實作為準；此頁主要提供快速落地的安裝/執行資訊。）


## 前置條件（Preconditions）

- 平台服務需正常（web/api/worker）
- tools 需可用（`/home/da40/charter/tools`）


## 需依環境替換（給外部單位）

以下參數通常因環境而異（請用 Environment Template / `.secrets` 注入）：

- `PROFILES_FILE` / `NOC_PROFILE` / `CUSTOMER_ID`
- `CPE_HOST` / `LAN_PARENT_IFACE` / `WIFI_IFACE` / `PING_IFACE`
- 任何 `*_PASSWORD` / `*_EMAIL` 一律不得寫死（用 `<fill>` 或 secrets）


## Key env quick reference

- `TOOLS_PATH`: `/home/da40/charter/tools`
- `PROFILES_FILE`: `/home/da40/charter/.secrets/noc_profiles.json`
- `NOC_PROFILE`: `SPECTRUM_INT`
- `CUSTOMER_ID`: `682d4e5179b80027cd6fb27e`
- `SSH_USER`: `operator`
- `SSH_PASSWORD`: `<fill>`


## manifest.yaml（節錄：env）

```yaml
name: A2844344_Continuously_executing_reboot
suite: stability
version: v2-professional-noc_profile-only-nodeid-cpeinfo
entrypoint: cycle_wrapper.py:run
env:
  CYCLES: '1'
  CYCLE_INTERVAL: '90'
  STOP_ON_FAIL: 0
  ORIGINAL_ENTRY: main_impl.py:run
  TOOLS_PATH: /home/da40/charter/tools
  REBOOT_MUTE_SECS: 60
  REBOOT_MUTE_WITH_LOCK: 0
  SSH_PASSWORD: <fill>
  NOC_BASE: https://piranha-int.tau.dev-charter.net
  NOC_PROFILE: SPECTRUM_INT
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
  CUSTOMER_ID: 682d4e5179b80027cd6fb27e
  BEARER: <fill>
  INSECURE: 0
  LOCATION_ID: ''
  CPE_BAUD: 115200
  CPE_USER: root
  CPE_PASSWORD: null
  POST_REBOOT_STATUS_WAIT_SEC: 120
  ENABLE_VERSION_GUARD: 1
  CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
  CPE_INFO_FWV_ARGS: -f "FW Version" --value
  ENABLE_SSH_PRE_SCAN: 1
  SSH_TIMEOUT_MIN: 120
  WAIT_AFTER_SSH_ENABLE_SEC: 60
  SSH_HOST_LAN: 192.168.1.1
  SSH_USER: operator
  CPE_SSH_TOOL: /home/da40/charter/tools/cpe_ssh.py
  SSH_TOOL_TIMEOUT: 15
  CPE_UPTIME_CMD: uptime
  SSH_SCAN_TIMEOUT_SEC: 60
  SSH_SCAN_INTERVAL_SEC: 2
  SSH_SCAN_PER_TRY_TIMEOUT_SEC: 2
  ENABLE_UPTIME_LOCAL_CHECK: 1
  ENABLE_UPTIME_COMPARE: 1
  NOC_API_CLI: /home/da40/charter/tools/noc_api_cli.py
  NOC_API_CLI_TIMEOUT_SEC: 30
  CLOUD_UPTIME_MODE: bootAt
  UPTIME_TOLERANCE_SEC: 120
  CLOUD_STATIC_LAG_SEC: 0
  FAIL_PULL_ENABLED: 1
  FAIL_WAIT_BEFORE_PULL_SEC: 60
  FAIL_PULL_SSH_ENABLED: 1
  FAIL_PULL_SSH_SCAN_TIMEOUT_SEC: 60
  FAIL_PULL_CLOUD_ENABLED: 1
  FAIL_AFTER_PULL_DELAY_SEC: 5
  FAIL_PULL_TIMEOUT_SEC: 300
  FAIL_PULL_LATEST_DIR: /tmp/logpull
  FAIL_PULL_PATTERN: '*.tar.gz'
  FAIL_PULL_DELETE_REMOTE: 0
  ENABLE_PARTITION_GUARD: 0
  PARTITION_FIELD: ''
  DEBUG: 1
```


## Run（建議 API 方式）

```bash
export CHARTER_BASE="http://<CONTROL_PC_IP>:5173"
SCRIPT_ID=<SCRIPT_ID_11F_140>
curl -sS -X POST "$CHARTER_BASE/api/scripts/$SCRIPT_ID/run" | python3 -m json.tool
```


## Artifacts / Evidence

```bash
RID=<RUN_ID>
curl -sS "$CHARTER_BASE/api/runs/$RID/log" > run_${RID}_log.json
curl -sS "$CHARTER_BASE/api/runs/$RID/log-archives" | python3 -m json.tool
# 若有 log archive：
curl -fsSL "$CHARTER_BASE/api/runs/$RID/log-archive" -o run_${RID}_cpe_log.tar.gz
```


## Cleanup

```bash
curl -sS -X DELETE "$CHARTER_BASE/api/runs/purge?older_than_days=0" | python3 -m json.tool
```
