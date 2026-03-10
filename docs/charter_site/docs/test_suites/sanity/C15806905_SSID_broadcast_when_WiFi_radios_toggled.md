# C15806905_SSID_broadcast_when_WiFi_radios_toggled

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_140=5204`
- 版本（manifest version）：`v16_platform_hint_manifest_fallback_warn`
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
- `WIFI_IFACE`: `wlx6cb0ce1ff230`


## manifest.yaml（節錄：env）

```yaml
name: C15806905_SSID_broadcast_when_WiFi_radios_toggled
suite: sanity
version: v16_platform_hint_manifest_fallback_warn
entrypoint: cycle_wrapper.py:run
env:
  CYCLES: '1'
  CYCLE_INTERVAL: '20'
  STOP_ON_FAIL: '1'
  ORIGINAL_ENTRY: main_impl_orig.py:run
  TOOLS_PATH: /home/da40/charter/tools
  CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
  CPE_SSH_TOOL: /home/da40/charter/tools/cpe_ssh.py
  NODE_ID_READY_CHECK: '1'
  NODE_ID_MAX_RETRIES: '10'
  NODE_ID_RETRY_INTERVAL_SEC: '5'
  CPE_READY_CHECK: '1'
  CPE_INFO_STATUS_CMD: cpe_info -status
  CPE_READY_MAX_RETRIES: '10'
  CPE_READY_RETRY_INTERVAL_SEC: '3'
  CPE_READY_REQUIRE_CLOUD: '1'
  PDU_RESET_ON_NOT_READY: '1'
  PDU_RESET_ACTION: reset
  PDU_RESET_TIMEOUT_SEC: '120'
  PDU_RESET_WAIT_SEC: '120'
  POST_PDU_STABILIZE_SEC: '40'
  ENABLE_SSH_FLOW: '1'
  SSH_ACTION: enable
  REQUIRE_SSH_READY: '1'
  SSH_READY_RETRY: '40'
  SSH_READY_WAIT_SEC: '3'
  SSH_READY_CMD: health
  NOC_BASE: https://piranha-int.tau.dev-charter.net
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
  NOC_PROFILE: SPECTRUM_INT
  CUSTOMER_ID: 682d4e5179b80027cd6fb27e
  NOC_EMAIL: ''
  NOC_PASSWORD: ''
  BEARER: <fill>
  INSECURE: '0'
  NOC_TIMEOUT_SEC: '30'
  NOC_RETRIES: '3'
  SSH_HOST_LAN: 192.168.1.1
  SSH_USER: operator
  SSH_PASSWORD: <fill>
  SSH_TIMEOUT_MIN: '120'
  CPE_USER: operator
  CPE_PASSWORD: <fill>
  CPE_SSH_TIMEOUT_SEC: '25'
  SSH_TOOL_TIMEOUT: '25'
  WIFI_IFACE: wlx6cb0ce1ff230
  WIFI_BAND: ''
  WIFI_CRED_PREFER: current
  WIFI_DHCP_TIMEOUT_SEC: '35'
  WIFI_IWD_TIMEOUT_SEC: '90'
  WIFI_POST_ENABLE_GRACE_SEC: '6'
  WIFI_CONNECT_RETRIES: '3'
  WIFI_CONNECT_RETRY_WAIT_SEC: '3'
  WIFI_TAKEOVER_ON_RETRY: '1'
  WIFI_FALLBACK_ANY_BAND: '1'
  WIFI_SSID: ''
  WIFI_PSK: ''
  WIFI_PSK_ENV: ''
  WIFI_NO_MAIN_DEFAULT: '1'
  WIFI_PBR_TABLE: '101'
  WIFI_PBR_FROM_IP: '0'
  WIFI_NOC_STATE_TIMEOUT_SEC: '180'
  WIFI_VIF_STATE_TIMEOUT_SEC: '180'
  WIFI_SCAN_TIMEOUT_SEC: '300'
  POLL_INTERVAL_SEC: '5'
  REQUIRE_SSH_VIF_OFF: '0'
  PING_TARGET: 192.168.1.1
  PING_COUNT: '2'
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
