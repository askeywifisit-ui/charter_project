# C15806902_WLAN_Client_connects_successfully_over_Default_SSID

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_140=5166`
- 版本（manifest version）：`v9.4-force-ping4-ip`
- Entrypoint：`cycle_wrapper.py:run`

> 本頁由工具依 11F_140 最新 export zip 自動產生/更新（2026-03-10）。

## 一句話說明

- Wi‑Fi/SSID 連線與 radio 行為驗證


## 你需要準備什麼（Preconditions）

- 平台服務正常：web/api/worker
- tools 可用：`/home/da40/charter/tools`
- secrets 不要寫死在 manifest（NOC/SSH/Warehouse 等一律用 `<fill>`/`.secrets`）


## 你只要改哪些參數（Top env）

- `TOOLS_PATH`: `/home/da40/charter/tools`
- `PROFILES_FILE`: `/home/da40/charter/.secrets/noc_profiles.json`
- `NOC_PROFILE`: `SPECTRUM_INT`
- `CUSTOMER_ID`: `682d4e5179b80027cd6fb27e`
- `SSH_USER`: `operator`
- `SSH_PASSWORD`: `<fill>`


## Run（API）

```bash
export CHARTER_BASE="http://<CONTROL_PC_IP>:5173"
SCRIPT_ID=<SCRIPT_ID_11F_140>
# 建議先確認 worker 正常
curl -fsSL "$CHARTER_BASE/api/runs/worker/status" | python3 -m json.tool
# 送出 run
curl -sS -X POST "$CHARTER_BASE/api/scripts/$SCRIPT_ID/run" | python3 -m json.tool
```


## 怎麼看結果（Evidence）

```bash
RID=<RUN_ID>
curl -sS "$CHARTER_BASE/api/runs/$RID/log" > run_${RID}_log.json
# 若 fail-hook 有產生 cpe logs
curl -sS "$CHARTER_BASE/api/runs/$RID/log-archives" | python3 -m json.tool
curl -fsSL "$CHARTER_BASE/api/runs/$RID/log-archive" -o run_${RID}_cpe_log.tar.gz
```


## Cleanup

```bash
# 清理已完成的 runs + workdir（避免磁碟累積）
curl -sS -X DELETE "$CHARTER_BASE/api/runs/purge?older_than_days=0" | python3 -m json.tool
```


??? note "manifest.yaml（節錄：常用 env）"

    ```yaml
    env:
      TOOLS_PATH: /home/da40/charter/tools
      PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
      NOC_PROFILE: SPECTRUM_INT
      CUSTOMER_ID: 682d4e5179b80027cd6fb27e
      SSH_USER: operator
      SSH_PASSWORD: <fill>
    ```


??? note "manifest.yaml（完整 env，已自動去敏）"

    ```yaml
    name: C15806902_WLAN_Client_connects_successfully_over_Default_SSID
    suite: sanity
    version: v9.4-force-ping4-ip
    entrypoint: cycle_wrapper.py:run
    env:
      CYCLES: '1'
      CYCLE_INTERVAL: '70'
      STOP_ON_FAIL: '1'
      ORIGINAL_ENTRY: main_impl_orig.py:run
      PRECOND_FACTORY_RESET: '1'
      FACTORY_RESET_WAIT_SEC: '90'
      FACTORY_RESET_MUTE_SECS: '60'
      AFTER_RESET_CPE_READY_MAX_RETRIES: '120'
      AFTER_RESET_CPE_READY_RETRY_INTERVAL_SEC: '5'
      PDU_RESET_ON_NOT_READY_AFTER_RESET: '1'
      TOOLS_PATH: /home/da40/charter/tools
      CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
      CPE_SSH_TOOL: /home/da40/charter/tools/cpe_ssh.py
      WIFI_IWD_TOOL: /home/da40/charter/tools/wifi_iwd.py
      WIFI_NM_TOOL: /home/da40/charter/tools/wifi_nm.py
      NODE_ID_MAX_RETRIES: '10'
      NODE_ID_RETRY_INTERVAL_SEC: '5'
      NOC_BASE: https://piranha-int.tau.dev-charter.net
      PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
      NOC_PROFILE: SPECTRUM_INT
      CUSTOMER_ID: 682d4e5179b80027cd6fb27e
      SSH_HOST_LAN: 192.168.1.1
      SSH_USER: operator
      SSH_PASSWORD: <fill>
      SSH_TOOL_TIMEOUT: '15'
      SSH_TIMEOUT_MIN: '120'
      CPE_READY_CHECK: '1'
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
      SSH_READY_RETRY: '20'
      SSH_READY_WAIT_SEC: '6'
      SSH_READY_INITIAL_WAIT_SEC: '20'
      SSH_READY_PORT_TIMEOUT_SEC: '5'
      SSH_READY_CMD: uptime
      CONSOLE_PASSWORD_FALLBACK: <fill>
      WIFI_METHOD: iwd
      WIFI_IWD_RESTORE_NM: '0'
      WIFI_IWD_UNMANAGED: '1'
      TEST_BANDS: 5g
      WIFI_BAND: ''
      WIFI_CRED_PREFER: default
      WIFI_TIMEOUT_SEC: auto
      WIFI_DHCP_TIMEOUT_SEC: auto
      WIFI_NM_RETRIES: '2'
      WIFI_DISCONNECT_ON_EXIT: '1'
      WIFI_CHECK_IPV6: auto
      WIFI_IPV6_WAIT_SEC: auto
      WIFI_IPV6_POLL_SEC: '2'
      WIFI_IPV6_SYSCTL_FIX: auto
      WIFI_IPV6_ACCEPT_RA: '2'
      WIFI_PING6_INTERNET: '0'
      WIFI_PING6_TARGET: ''
      WIFI_PING_ROUTER: 192.168.1.1
      WIFI_PING_TARGET: 8.8.8.8
      WIFI_PING_INTERNET: '1'
      WIFI_PING_COUNT: '3'
      WIFI_PING_TIMEOUT_SEC: '5'
    ```
