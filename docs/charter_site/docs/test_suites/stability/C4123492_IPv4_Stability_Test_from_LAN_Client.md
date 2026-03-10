# C4123492_IPv4_Stability_Test_from_LAN_Client

- Suite: **stability**
- Script ID（可能因 delete/import 變動）：`11F_140=5121`
- 版本（manifest version）：`v12-lanclient-stability-single-pingiface`
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
- `CPE_HOST`: `192.168.1.1`
- `SSH_PASSWORD`: `<fill>`


## manifest.yaml（節錄：env）

```yaml
name: C4123492_IPv4_Stability_Test_from_LAN_Client
suite: stability
version: v12-lanclient-stability-single-pingiface
entrypoint: cycle_wrapper.py:run
env:
  CYCLES: '1'
  CYCLE_INTERVAL: '30'
  STOP_ON_FAIL: '0'
  ORIGINAL_ENTRY: main_impl.py:run
  PRECONDITION_FIRST_CYCLE: '1'
  TOOLS_PATH: /home/da40/charter/tools
  NOC_PROFILE: SPECTRUM_INT
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
  CPE_HOST: 192.168.1.1
  CPE_SSH_PORT: '22'
  CPE_SSH_USER: operator
  SSH_PASSWORD: <fill>
  SSH_PASSWORD_DEFAULT: <fill>
  REQUIRE_SSH_READY: '1'
  SSH_PROBE_CMD: uptime
  SSH_SCAN_TIMEOUT_SEC: '30'
  SSH_SCAN_INTERVAL_SEC: '2'
  SSH_ENABLE_RETRIES: '2'
  WAIT_AFTER_SSH_ENABLE_SEC: '60'
  SSH_TIMEOUT_MIN: '120'
  CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
  CPE_INFO_TIMEOUT_SEC: '30'
  CPE_READY_RETRIES_BEFORE_RESET: '3'
  CPE_READY_RETRIES_AFTER_RESET: '6'
  CPE_READY_RETRY_SLEEP_SEC: '10'
  DO_PDU_RESET_ON_READY_FAIL: '1'
  PDU_WAIT_SEC: '120'
  LAN_PING_BACKEND: plain
  LAN_MACVLAN_PING_COUNT: '20'
  LAN_MACVLAN_PING_TIMEOUT_SEC: '2'
  PBR_IFACE: ''
  PBR_SRC_IP: ''
  PBR_GW: 192.168.1.1
  PBR_SUBNET: 192.168.1.0/24
  PBR_TABLE_ID: '100'
  PBR_PRIO_FROM: '1000'
  PBR_PRIO_TO: '1001'
  PROBE_IFACE: ''
  PROBE_SRC_IP: ''
  LAN_PING_CPE_COUNT: '20'
  LAN_PING_CPE_DEADLINE_SEC: '20'
  CPE_WAN_GATEWAY: 172.14.1.1
  CPE_PING_GW_COUNT: '10'
  LOSS_TRIGGER_PCT: '10'
  CONSEC_FAIL_TRIGGER_N: '3'
  LOGPULL_ON_TRIGGER: '1'
  LOGPULL_LATEST_DIR: /tmp/logpull
  LOGPULL_PATTERN: '*.tar.gz'
  LOG_INCLUDE_TS: '0'
  CUSTOMER_ID: 682d4e5179b80027cd6fb27e
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
