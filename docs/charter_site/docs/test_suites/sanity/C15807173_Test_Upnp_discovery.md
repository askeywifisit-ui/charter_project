# C15807173_Test_Upnp_discovery

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_140=5215`
- 版本（manifest version）：`v1-upnp-ready-wait-retry-soap-fault`
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
name: C15807173_Test_Upnp_discovery
suite: sanity
version: v1-upnp-ready-wait-retry-soap-fault
entrypoint: cycle_wrapper.py:run
env:
  CYCLES: '1'
  CYCLE_INTERVAL: '30'
  STOP_ON_FAIL: 1
  ORIGINAL_ENTRY: main_impl_orig.py:run
  TOOLS_PATH: /home/da40/charter/tools
  METRICS_TOOL: /home/da40/charter/tools/cpe_metrics_agent_serial.py
  CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
  CPE_SSH_TOOL: /home/da40/charter/tools/cpe_ssh.py
  USE_SERIAL_NODEID: '0'
  CPE_BAUD: 115200
  CPE_USER: root
  CPE_PASSWORD: null
  NOC_BASE: https://piranha-int.tau.dev-charter.net
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
  NOC_PROFILE: SPECTRUM_INT
  CUSTOMER_ID: 682d4e5179b80027cd6fb27e
  NOC_EMAIL: ''
  NOC_PASSWORD: ''
  NOC_BEARER: <fill>
  NOC_INSECURE: '0'
  SSH_HOST_LAN: 192.168.1.1
  SSH_USER: operator
  SSH_PASSWORD: <fill>
  SSH_TOOL_TIMEOUT: 20
  SSH_ENABLE_AT_START: '1'
  SSH_TIMEOUT_MIN: '120'
  SSH_PORT_MAX_RETRIES: '10'
  SSH_PORT_INTERVAL_SEC: '3'
  SSH_PORT_CHECK_TIMEOUT: '3'
  SSH_PORT_TIMEOUT_SEC: '240'
  LAN_IFACE: ''
  UPNP_ENABLE_AT_START: '1'
  UPNP_DISABLE_AT_END: '1'
  UPNP_APPLY_WAIT_SEC: '40'
  MINIUPNPD_RETRIES: '8'
  MINIUPNPD_RETRY_INTERVAL_SEC: '5'
  MINIUPNPD_STOP_RETRIES: '10'
  MINIUPNPD_STOP_RETRY_INTERVAL_SEC: '3'
  EXPECT_REBOOT_AFTER_UPNP_ENABLE: '1'
  EXPECT_REBOOT_AFTER_UPNP_DISABLE: '1'
  REBOOT_MUTE_SECS: '120'
  REBOOT_MUTE_WITH_LOCK: '1'
  SERIAL_MUTE_TOOL: /home/da40/charter/tools/serial_mute.py
  CPE_INFO_STATUS_TIMEOUT_SEC: '40'
  CPE_READY_CHECK: '1'
  CPE_READY_MAX_RETRIES: '30'
  CPE_READY_RETRY_INTERVAL_SEC: '6'
  CPE_READY_REQUIRE_CLOUD: '1'
  MINIUPNPD_CMD: ps | grep miniupnpd
  UPNP_IGD_TESTER: /home/da40/charter/tools/upnp_igd_tester.py
  UPNP_IGD_TIMEOUT_SEC: '60'
  UPNP_IGD_TEST_PORT: '54321'
  UPNP_IGD_PROTOCOL: TCP
  REQUIRE_SSDP_MSEARCH_ON: '1'
  REQUIRE_SSDP_MSEARCH_OFF: '1'
  SSDP_MSEARCH_TIMEOUT_SEC: '3'
  SSDP_MSEARCH_RETRIES: '5'
  SSDP_MSEARCH_RETRY_SLEEP_SEC: '5'
  REQUIRE_SSDP_ALIVE: '0'
  REQUIRE_SSDP_BYEBYE: '0'
  TCPDUMP_TIMEOUT_ON_SEC: '180'
  TCPDUMP_TIMEOUT_OFF_SEC: '180'
  TCPDUMP_RETRIES: '3'
  TCPDUMP_RETRY_SLEEP_SEC: '10'
  TCPDUMP_FILTER: udp port 1900
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
