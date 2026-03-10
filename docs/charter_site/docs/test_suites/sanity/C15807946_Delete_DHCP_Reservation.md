# C15807946_Delete_DHCP_Reservation

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_140=5216`
- 版本（manifest version）：`v1-cpe-gate-noc-evidence-only-precond-baseline-ipinuse-retry-customersafe`
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
name: C15807946_Delete_DHCP_Reservation
suite: sanity
version: v1-cpe-gate-noc-evidence-only-precond-baseline-ipinuse-retry-customersafe
entrypoint: cycle_wrapper.py:run
env:
  TEST_NAME: C15807946_Delete_DHCP_Reservation
  CYCLE_INTERVAL_SEC: '60'
  STOP_ON_FAIL: '1'
  CYCLES: '1'
  CYCLE_INTERVAL: '70'
  TOOLS_PATH: /home/da40/charter/tools
  NOC_PROFILE: SPECTRUM_INT
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
  CUSTOMER_ID: 682d4e5179b80027cd6fb27e
  CPE_HOST: 192.168.1.1
  CPE_SSH_USER: operator
  SSH_PASSWORD: <fill>
  SSH_READY_CMD: uptime
  CPE_SSH_PORT: '22'
  SSH_SCAN_TIMEOUT_SEC: '30'
  SSH_SCAN_INTERVAL_SEC: '2'
  CPE_SSH_TIMEOUT_SEC: '30'
  SSH_PASSWORD_DEFAULT: <fill>
  SSH_ENABLE_RETRIES: '2'
  WAIT_AFTER_SSH_ENABLE_SEC: '60'
  POST_PDU_STABILIZE_SEC: '40'
  SERIAL_MUTE_SEC: '60'
  CLOUD_READY_TIMEOUT_SEC: '30'
  CLOUD_READY_INTERVAL_SEC: '3'
  NODE_ID_MAX_RETRIES: '10'
  NODE_ID_RETRY_INTERVAL_SEC: '3'
  SSH_ENABLE_ATTEMPTS: '2'
  SSH_ENABLE_WAIT_SEC: '20'
  LAN_TEST_IFACE: auto
  LAN_TEST_MAC: ''
  LAN_PING_TARGET: google.com
  LAN_RENEW_TIMEOUT_SEC: '120'
  TEST_HOSTNAME: lan_test0
  TEST_RESERVED_IP: 192.168.1.225
  CLEAR_CONFLICTING_IP_RESERVATION: '1'
  CLEAR_ALL_NOC_DHCP_RESERVATIONS: '0'
  CLEAR_ALL_NOC_DHCP_RESERVATIONS_HOSTNAME_PREFIX: lan_test
  AUTO_PICK_FREE_IP: '1'
  IP_IN_USE_RETRY_MAX: '10'
  DHCP_DUMP_RETRIES: '8'
  DHCP_DUMP_RETRY_WAIT_SEC: '5'
  LEASE_WAIT_TIMEOUT_SEC: '180'
  LEASE_WAIT_INTERVAL_SEC: '10'
  DELETE_VERIFY_TIMEOUT_SEC: '240'
  DELETE_VERIFY_INTERVAL_SEC: '10'
  EXPECT_NO_NOC_RESERVATIONS_AFTER_DELETE: '1'
  EXPECT_NO_CPE_RESERVATIONS_AFTER_DELETE: '1'
  LAN_RENEW_AFTER_DELETE: '1'
  LAN_RENEW_AFTER_DELETE_ATTEMPTS: '2'
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
