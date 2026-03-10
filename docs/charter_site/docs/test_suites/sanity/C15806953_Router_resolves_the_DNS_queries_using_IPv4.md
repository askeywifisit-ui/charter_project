# C15806953_Router_resolves_the_DNS_queries_using_IPv4

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_140=5168`
- 版本（manifest version）：`v2-DNS_queries_IPv4`
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
name: C15806953_Router_resolves_the_DNS_queries_using_IPv4
suite: sanity
version: v2-DNS_queries_IPv4
entrypoint: cycle_wrapper.py:run
env:
  CYCLES: '1'
  CYCLE_INTERVAL: 70
  STOP_ON_FAIL: 1
  ORIGINAL_ENTRY: main_impl_orig.py:run
  TOOLS_PATH: /home/da40/charter/tools
  METRICS_TOOL: /home/da40/charter/tools/cpe_metrics_agent_serial.py
  CPE_BAUD: '115200'
  CPE_USER: root
  CPE_PASSWORD: ''
  CPE_IFACE: br-wan
  NOC_BASE: https://piranha-int.tau.dev-charter.net
  NOC_EMAIL: <fill>
  NOC_PASSWORD: <fill>
  CUSTOMER_ID: 682d4e5179b80027cd6fb27e
  BEARER: <fill>
  INSECURE: 0
  API_BASE: http://127.0.0.1:8080
  DISABLE_INTERNAL_LOGPULL: '1'
  USE_CLOUD_SSH: '1'
  CPE_LOG_TIMEOUT_SEC: '240'
  NOC_PROFILE: SPECTRUM_INT
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
  ENABLE_SSH_FLOW: 1
  SSH_ENABLE_RETRIES: 3
  SSH_SCAN_TIMEOUT_SEC: 30
  SSH_USER: operator
  SSH_PASSWORD: <fill>
  SSH_TIMEOUT_MIN: '120'
  CPE_HEALTH_HOST: 192.168.1.1
  CPE_HEALTH_PORT: '22'
  SSH_PORT_CHECK_TIMEOUT: '3'
  ENABLE_SPEEDTEST: 0
  ENABLE_WIFI_TEST: 0
  ENABLE_LTE_TEST: 0
  ENABLE_HEALTH_CHECK: 0
  ENABLE_DNS_CHECK: 1
  TARGET: www.google.com
  SECOND: www.o2.de
  EXPECT_A_MIN: 1
  EXPECT_AAAA_MIN: 1
  RETRIES: 3
  INTERVAL_SEC: 3
  DNS_SSH_TIMEOUT_SEC: 30
  DNS_INVALID_IPS: 172.14.1.1, 127.0.0.53,223.255.255.1, 223.255.255.1
  DEBUG_DNS: '0'
  DEBUG_SHOW_CMD: '0'
  SAVE_DNS_RESULTS: '1'
  DNS_RESULTS_FILE: dns_results.json
  NODE_ID_MAX_TRIES: 3
  NODE_ID_INTERVAL_SEC: 2
  NODE_ID_CMD_TIMEOUT_SEC: 15
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
