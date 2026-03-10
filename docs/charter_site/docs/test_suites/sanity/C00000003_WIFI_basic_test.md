# C00000003_WIFI_basic_test

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_140=5164`
- 版本（manifest version）：`v2-noc-context-retry-timeout-tolerant`
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
name: C00000003_WIFI_basic_test
suite: sanity
version: v2-noc-context-retry-timeout-tolerant
entrypoint: cycle_wrapper.py:run
env:
  CYCLES: '1'
  CYCLE_INTERVAL: '10'
  STOP_ON_FAIL: 1
  ORIGINAL_ENTRY: main_impl_orig.py:run
  TOOLS_PATH: /home/da40/charter/tools
  CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
  CPE_SSH_TOOL: /home/da40/charter/tools/cpe_ssh.py
  WIFI_IWD_TOOL: /home/da40/charter/tools/wifi_iwd.py
  WIFI_NM_TOOL: /home/da40/charter/tools/wifi_nm.py
  NODE_ID_MAX_RETRIES: 10
  NODE_ID_RETRY_INTERVAL_SEC: 5
  NOC_BASE: https://piranha-int.tau.dev-charter.net
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
  NOC_PROFILE: SPECTRUM_INT
  CUSTOMER_ID: 682d4e5179b80027cd6fb27e
  SSH_HOST_LAN: 192.168.1.1
  SSH_USER: operator
  SSH_PASSWORD: <fill>
  SSH_TOOL_TIMEOUT: 15
  SSH_TIMEOUT_MIN: 120
  CPE_READY_CHECK: 1
  CPE_INFO_STATUS_CMD: cpe_info -status
  CPE_READY_MAX_RETRIES: 10
  CPE_READY_RETRY_INTERVAL_SEC: 3
  CPE_READY_REQUIRE_CLOUD: 1
  PDU_RESET_ON_NOT_READY: 1
  PDU_RESET_ACTION: reset
  PDU_RESET_TIMEOUT_SEC: 120
  PDU_RESET_WAIT_SEC: 120
  POST_PDU_STABILIZE_SEC: 40
  ENABLE_SSH_FLOW: 1
  SSH_ACTION: enable
  REQUIRE_SSH_READY: 1
  SSH_READY_RETRY: 2
  SSH_READY_WAIT_SEC: 2
  SSH_READY_CMD: uptime
  WIFI_METHOD: auto
  WIFI_BAND: 5g
  WIFI_CRED_PREFER: current
  WIFI_TIMEOUT_SEC: '45'
  WIFI_NM_RETRIES: '2'
  WIFI_DISCONNECT_ON_EXIT: '1'
  WIFI_PING_ROUTER: 192.168.1.1
  WIFI_PING_TARGET: www.google.com
  WIFI_PING_INTERNET: 1
  WIFI_PING_COUNT: 3
  WIFI_PING_TIMEOUT_SEC: 5
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
