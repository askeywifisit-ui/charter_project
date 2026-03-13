# C15807121_Customer_page_should_load_using_Domain_Name_on_LAN_Client

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_140=5171`
- 版本（manifest version）：`v25-internetstatus-transient-poll`
- Entrypoint：`rg_cycle_wrapper.py:run`

> 本頁由工具依 11F_140 最新 export zip 自動產生/更新（2026-03-10）。

## 一句話說明

- （依腳本實作為準）


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


??? note "manifest.yaml（流程參數完整；帳密/API key 已遮蔽）"

    ```yaml
    name: C15807121_Customer_page_should_load_using_Domain_Name_on_LAN_Client
    suite: sanity
    version: v25-internetstatus-transient-poll
    entrypoint: rg_cycle_wrapper.py:run
    env:
      CYCLES: '1'
      CYCLE_INTERVAL: '70'
      STOP_ON_FAIL: 1
      ORIGINAL_ENTRY: main_impl_orig.py:run
      CPE_READY_CHECK: '1'
      CPE_READY_REQUIRE_CLOUD: '1'
      CPE_READY_MAX_RETRIES: '5'
      CPE_READY_RETRY_INTERVAL_SEC: '3'
      PDU_RESET_ON_NOT_READY: '1'
      PDU_RESET_SCRIPT: /home/da40/charter/tools/pdu_outlet2.py
      PDU_RESET_ACTION: reset
      PDU_RESET_TIMEOUT_SEC: '600'
      PDU_RESET_WAIT_SEC: '120'
      TOOLS_PATH: /home/da40/charter/tools
      METRICS_TOOL: /home/da40/charter/tools/cpe_metrics_agent_serial.py
      NODE_ID_MAX_RETRIES: '10'
      NODE_ID_FALLBACK_CPE_INFO: '1'
      CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
      NODE_ID_RETRY_INTERVAL_SEC: '3'
      CPE_BAUD: '115200'
      CPE_USER: root
      CPE_PASSWORD: ''
      CUSTOMER_ID: 682d4e5179b80027cd6fb27e
      NOC_PROFILE: SPECTRUM_INT
      PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
      NOC_BASE: https://piranha-int.tau.dev-charter.net
      NOC_EMAIL: ''
      NOC_PASSWORD: ''
      BEARER: <fill>
      INSECURE: 0
      WEB_HTTP_URLS: http://MyRouter
      WEB_EXPECT_HTTPS_URLS: https://myrouter/
      PRIMARY_FETCH_HTTPS_URL: https://myrouter/cgi-bin/index.cgi
      CHECK_WAN_IPV4: '1'
      COMPARE_WEB_VS_AWLAN: '1'
      CHECK_WAN_IPV4_MATCH: '1'
      CHECK_WAN_MAC_MATCH: '1'
      CHECK_WAN_IPV6_MATCH: '1'
      SKIP_IPV6_IF_NO_GLOBAL: '1'
      CHECK_INTERNET_STATUS_PING: '1'
      PING_TARGETS: 1.1.1.1,8.8.8.8
      PING_COUNT: '2'
      PING_TIMEOUT_SEC: '3'
      PING_STRICT: '0'
      WEB_TIMEOUT_SEC: '25'
      WEB_RETRIES: '10'
      WEB_SLEEP_SEC: '3'
      REDIRECT_MATCH_MODE: strict
      ALLOW_RELATIVE_LOCATION: '1'
      CHECK_HTTP_REDIRECT: '1'
      REDIRECT_CHECK_FINAL: '1'
      REDIRECT_FINAL_TIMEOUT_SEC: '12'
      REDIRECT_RETRIES: '10'
      REDIRECT_SLEEP_SEC: '3'
      CHECK_DOMAIN_RESOLVE: '1'
      EXPECTED_LAN_IP: 192.168.1.1
      DOMAIN_RESOLVE_STRICT: '1'
      DOMAIN_RESOLVE_RETRIES: '10'
      DOMAIN_RESOLVE_SLEEP_SEC: '3'
      ENABLE_SSH_VIA_NOC: '1'
      SSH_ENABLE_TIMEOUT_MIN: '30'
      SSH_ENABLE_PASSWORD: <fill>
      SSH_ENABLE_WAIT_SEC: '10'
      VALIDATE_MACS_VIA_SSH: '1'
      MAC_VALIDATION_STRICT: '1'
      WAN_IFACES: br-wan
      WAN_IFACE: br-wan
      LAN_IFACES: br-home,BR_LAN,br-lan
      ALLOW_WIFI5_WIFI6_SWAP: '1'
      WLAN5_IFACES: wifi1
      WLAN6_IFACES: wifi2
      SSH_HOST: 192.168.1.1
      SSH_USER: operator
      SSH_PASSWORD: <fill>
      SSH_TIMEOUT_SEC: '30'
      SSH_READY_RETRIES: '10'
      SSH_READY_SLEEP_SEC: '3'
      SSH_READY_TIMEOUT_SEC: '8'
      SSH_READY_CMD: uptime
      MACS_IFACES: br-wan,br-home,wifi0,wifi1,wifi2
      SSH_MACS_RETRIES: '3'
      SSH_MACS_SLEEP_SEC: '3'
      SSH_MACS_TIMEOUT_SEC: '30'
      SSH_MACS_MAX_TIMEOUT_SEC: '90'
      MACS_USE_TOOL_ONLY: '0'
      SSH_IFCONFIG_RETRIES: '3'
      SSH_IFCONFIG_SLEEP_SEC: '3'
      SSH_IFCONFIG_MAX_TIMEOUT_SEC: '60'
      REQUIRED_FIELDS: Serial Number,Model,FW Version,IPv4 Address
      CHECK_DEFAULT_B64: '0'
      EXPECT_SAME_AS_DEFAULT: '0'
      DO_FACTORY_RESET: '1'
      FR_SETTLE_WAIT_SEC: '120'
      RESET_MUTE_SECS: '60'
      RESET_MUTE_WITH_LOCK: '0'
      FACTORY_RESET_MUTE_SECS: ''
      FACTORY_RESET_MUTE_WITH_LOCK: '0'
      FACTORY_RESET_MUTE_LOCK_TIMEOUT_SEC: '5'
      CHANGE_WIFI: '0'
      NEW_WIFI_SSID: QA_Auto_SSID
      NEW_WIFI_PASSWORD: <fill>
      WIFI_APPLY_WAIT_SEC: '60'
      SSH_PORT: '22'
      SSH_PORT_SCAN_TIMEOUT_SEC: '60'
      SSH_PORT_SCAN_INTERVAL_SEC: '2'
      SSH_ENABLE_ATTEMPTS: '2'
      WAIT_AFTER_SSH_ENABLE_SEC: '60'
      ALLOW_WEB_INTERNET_TRANSIENT: '1'
      INTERNET_STATUS_POLL_RETRIES: '10'
      INTERNET_STATUS_POLL_SLEEP_SEC: '3'
    ```
