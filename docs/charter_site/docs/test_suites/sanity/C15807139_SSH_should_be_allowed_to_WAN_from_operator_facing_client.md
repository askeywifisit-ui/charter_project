# C15807139_SSH_should_be_allowed_to_WAN_from_operator_facing_client

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_140=5178`
- 版本（manifest version）：`v8`
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
name: C15807139_SSH_should_be_allowed_to_WAN_from_operator_facing_client
suite: sanity
version: v8
entrypoint: cycle_wrapper.py:run
env:
  IPV4_TO_IPV6_SLEEP_SEC: 3
  CYCLES: '1'
  CYCLE_INTERVAL: '70'
  STOP_ON_FAIL: 1
  ORIGINAL_ENTRY: main_impl_orig.py:run
  TOOLS_PATH: /home/da40/charter/tools
  CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
  CPE_SSH_TOOL: /home/da40/charter/tools/cpe_ssh.py
  NODE_ID_USE_SERIAL: 0
  CUSTOMER_ID: 682d4e5179b80027cd6fb27e
  NOC_PROFILE: SPECTRUM_INT
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
  SSH_USER: operator
  SSH_PASSWORD: <fill>
  SSH_TIMEOUT_MIN: 120
  SSH_HOST_LAN: 192.168.1.1
  AUTO_SSH_ENABLE: 1
  REQUIRE_SSH_READY: 1
  SSH_ENABLE_ATTEMPTS: 2
  SSH_READY_WAIT_SEC: 30
  SSH_TOOL_TIMEOUT: 15
  ENABLE_SSH_FLOW: 1
  LAN_SSH_REQUIRED: 1
  WAN_SSH_TIMEOUT_SEC: 30
  SSH_ENABLE_WAIT_SEC: 10
  WAN_SSH_READY_RETRIES: 10
  WAN_SSH_READY_INTERVAL_SEC: 3
  WAN_SSH_READY_TIMEOUT_SEC: 3
  WAN_SSH_LOGIN_RETRIES: 8
  WAN_SSH_LOGIN_INTERVAL_SEC: 5
  WAN_SSH_LOGIN_TIMEOUT_SEC: 10
  ENABLE_IPV6: auto
  IPV6_REQUIRED: 1
  SKIP_IPV6: 0
  CPE_LAN_IFACE: br-home
  CLIENT_WAN_IFACE: auto
  CLIENT_LAN_IFACE: auto
  WAN_SSH_BIND_SRC4: auto
  WAN_SSH_BIND_SRC6: auto
  WAN_SSH_BIND_IFACE: auto
  REQUIRE_OPERATOR_FACING: 0
  CPE_READY_CHECK: '1'
  CPE_INFO_STATUS_CMD: cpe_info -status
  CPE_READY_MAX_RETRIES: '5'
  CPE_READY_RETRY_INTERVAL_SEC: '3'
  CPE_READY_REQUIRE_CLOUD: '1'
  PDU_RESET_ON_NOT_READY: '1'
  PDU_RESET_ACTION: reset
  PDU_RESET_WAIT_SEC: '120'
  CPE_READY_TIMEOUT_SEC: '60'
  NODE_ID_MAX_RETRIES: 10
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
