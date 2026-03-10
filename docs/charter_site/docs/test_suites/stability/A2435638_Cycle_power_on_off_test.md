# A2435638_Cycle_power_on_off_test

- Suite: **stability**
- Script ID（可能因 delete/import 變動）：`11F_140=5115`
- 版本（manifest version）：`v7-ssh-enable-profile-compat`
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
- `SSH_USER`: `operator`
- `SSH_PASSWORD`: `<fill>`


## manifest.yaml（節錄：env）

```yaml
name: A2435638_Cycle_power_on_off_test
suite: stability
version: v7-ssh-enable-profile-compat
entrypoint: cycle_wrapper.py:run
env:
  CYCLES: '1'
  CYCLE_INTERVAL: '60'
  STOP_ON_FAIL: '0'
  ORIGINAL_ENTRY: main_impl.py:run
  CPE_BAUD: '115200'
  CPE_USER: root
  CPE_PASSWORD: ''
  CPE_IFACE: br-wan
  API_BASE: http://127.0.0.1:8080
  SERIAL_SETTLE_MS: '300'
  STEP_WAIT_BEFORE_MS: '0'
  STEP_WAIT_AFTER_MS: '100'
  WAIT_AFTER_POWER_OFF_MS: '1000'
  WAIT_AFTER_POWER_ON_MS: '3000'
  READY_RETRIES: '60'
  READY_INTERVAL_MS: '1000'
  POWER_OFF_CMD: ''
  POWER_ON_CMD: ''
  POWER_CMD_TIMEOUT_SEC: '20'
  CPE_PING1: 8.8.8.8
  RETRIES: '60'
  INTERVAL_SEC: '1'
  STRICT_PING: '0'
  SHOW_METRICS: '1'
  ECHO_METRICS: '1'
  ECHO_MAX_LINES: '12'
  DEBUG_METRICS: '0'
  POWER_OFF_SEC: '10'
  SETTLE_SEC: '120'
  CHECK_CMD: ''
  FINAL_STATUS_CHECK: '1'
  CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
  CPE_INFO_TIMEOUT_SEC: '90'
  TOOLS_PATH: /home/da40/charter/tools
  CPE_SSH_TOOL: /home/da40/charter/tools/cpe_ssh.py
  SSH_HOST_LAN: 192.168.1.1
  SSH_USER: operator
  SSH_PASSWORD: <fill>
  REQUIRE_SSH_READY: '1'
  AUTO_SSH_ENABLE: '1'
  NOC_PROFILE: SPECTRUM_INT
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
  SSH_TIMEOUT_MIN: '120'
  SSH_READY_WAIT_SEC: '90'
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
