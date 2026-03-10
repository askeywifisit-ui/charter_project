# C00000002_SSH_disable_test

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_140=5163`
- 版本（manifest version）：`v1`
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


## manifest.yaml（節錄：env）

```yaml
name: C00000002_SSH_disable_test
suite: sanity
version: v1
entrypoint: cycle_wrapper.py:run
env:
  CYCLES: '1'
  CYCLE_INTERVAL: '70'
  STOP_ON_FAIL: '1'
  ORIGINAL_ENTRY: main_impl.py:run
  TOOLS_PATH: /home/da40/charter/tools
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
  NOC_PROFILE: SPECTRUM_INT
  NOC_BASE: ''
  CUSTOMER_ID: 682d4e5179b80027cd6fb27e
  NOC_EMAIL: ''
  NOC_PASSWORD: ''
  LOCATION_ID: ''
  BEARER: <fill>
  INSECURE: '0'
  CPE_HOST: 192.168.1.1
  CPE_SSH_PORT: '22'
  CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
  CPE_INFO_TIMEOUT_SEC: '30'
  CPE_READY_MAX_RETRIES: '10'
  CPE_READY_RETRY_SLEEP_SEC: '30'
  WAIT_AFTER_SSH_DISABLE_SEC: '60'
  SSH_DISABLE_VERIFY: '1'
  SSH_DISABLE_VERIFY_TIMEOUT_SEC: '120'
  SSH_DISABLE_VERIFY_INTERVAL_SEC: '2'
  LOG_INCLUDE_TS: '0'
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
