# C24541454_Multiple_reboot_stress

- Suite: **stability**
- Script ID（可能因 delete/import 變動）：`11F_140=5119`
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
name: C24541454_Multiple_reboot_stress
suite: stability
version: v2-professional-noc_profile-only-nodeid-cpeinfo
entrypoint: cycle_wrapper.py:run
env:
  CYCLES: '1'
  CYCLE_INTERVAL: 30
  STOP_ON_FAIL: 1
  ORIGINAL_ENTRY: main_impl_orig.py:run
  TOOLS_PATH: /home/da40/charter/tools
  NODE_ID_MAX_RETRIES: 30
  NODE_ID_RETRY_INTERVAL_SEC: 2
  CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
  CPE_BAUD: 115200
  CPE_USER: root
  CPE_PASSWORD: null
  NOC_BASE: https://piranha-int.tau.dev-charter.net
  SSH_USER: operator
  SSH_PASSWORD: <fill>
  SSH_TIMEOUT_MIN: 120
  SSH_REENABLE_EACH_CYCLE: 0
  SSH_HOST_LAN: 192.168.1.1
  WAN_SSH_REQUIRED: 0
  LAN_SSH_REQUIRED: 1
  CPE_SSH_TOOL: /home/da40/charter/tools/cpe_ssh.py
  SSH_TOOL_TIMEOUT: 15
  USE_CLOUD_SSH: '1'
  CPE_LOG_TIMEOUT_SEC: '240'
  NOC_PROFILE: SPECTRUM_INT
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
  CUSTOMER_ID: 682d4e5179b80027cd6fb27e
  SSH_ACTION: enable
  ENABLE_SSH_FLOW: 0
  ENABLE_REBOOT_TEST: 1
  REBOOT_DELAY_SEC: 2
  REBOOT_MUTE_SECS: 60
  REBOOT_MUTE_WITH_LOCK: 1
  POST_REBOOT_STATUS_WAIT_SEC: 120
  CPE_STATUS_MAX_RETRIES: 3
  CPE_STATUS_RETRY_INTERVAL_SEC: 30
  ENABLE_CPE_STATUS_CHECK: 1
  ENABLE_DNS_CHECK: 0
  TARGET: www.google.com
  SECOND: cloudflare.com
  EXPECT_A_MIN: 1
  EXPECT_AAAA_MIN: 1
  RETRIES: 3
  INTERVAL_SEC: 3
  DNS_SSH_TIMEOUT_SEC: 30
  PRECONDITION_FIRST_CYCLE: 1
  AUTO_SSH_ENABLE: 1
  REQUIRE_SSH_READY: 1
  SSH_ENABLE_RETRIES: 2
  SSH_SCAN_TIMEOUT_SEC: 60
  SSH_SCAN_INTERVAL_SEC: 2
  WAIT_AFTER_SSH_ENABLE_SEC: 60
  CPE_READY_MAX_RETRIES: 10
  CPE_READY_RETRY_INTERVAL_SEC: 3
  CPE_READY_CMD_TIMEOUT_SEC: 30
  PDU_RESET_ACTION: reset
  PDU_RESET_WAIT_SEC: 120
  PDU_RESET_TIMEOUT_SEC: 600
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
