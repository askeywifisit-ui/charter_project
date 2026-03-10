# C15807242_Warehouse_Web_Page_should_load_with_Domain_Name

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_131=60` / `11F_140(current)=5209`
- 風險等級（對 DUT 影響）：**HIGH**

## 目的（Purpose）
驗證從 LAN client 以 IP/IPv6 link-local/Domain name 開啟 Customer/Warehouse Web Page。

## 前置條件（Preconditions）
- CPE/Cloud 需可連線（Internet/Cloud Connected）
- 需要的工具：`/home/da40/charter/tools`

## 測試行為摘要（What it does）
- LAN client 取得 IP
- DNS/Domain（若需要）
- HTTP/HTTPS 請求頁面並檢查回應

## 主要參數（manifest env 重要值）
- CYCLES: `1`
- INTERVAL: `70`
- STOP_ON_FAIL: `1`

### 需依環境替換（給外部單位）
請參考 **Environment Template**，常見需替換：
- `TOOLS_PATH` / `PROFILES_FILE` / `NOC_PROFILE` / `CUSTOMER_ID`
- `CPE_HOST` / `LAN_PARENT_IFACE` / `WIFI_IFACE` / `PING_IFACE`

## manifest.yaml（節錄）
```yaml
name: C15807242_Warehouse_Web_Page_should_load_with_Domain_Name
version: v3_mac_validate_rounds
suite: sanity
entrypoint: cycle_wrapper.py:run
entry: cycle_wrapper.py:run
env:
  # =========================
  # [Wrapper / 循環控制]
  # =========================
  CYCLES: '1'
  CYCLE_INTERVAL: '70'
  STOP_ON_FAIL: 1
  ORIGINAL_ENTRY: main_impl_orig.py:run

  # =========================
  # [CPE Ready Precondition + PDU Reset]
  # - cycle_wrapper 會在第 1 輪前先做 cpe_info -status 檢查
  # - 若未 ready 且啟用 PDU_RESET_ON_NOT_READY，會執行 PDU_RESET_SCRIPT reset
  # =========================
  CPE_READY_CHECK: '1'
  CPE_READY_REQUIRE_CLOUD: '1'
  CPE_READY_MAX_RETRIES: '5'
  CPE_READY_RETRY_INTERVAL_SEC: '3'
  PDU_RESET_ON_NOT_READY: '1'
  PDU_RESET_SCRIPT: /home/da40/charter/tools/pdu_outlet2.py
  PDU_RESET_ACTION: reset
  PDU_RESET_TIMEOUT_SEC: '600'
  PDU_RESET_WAIT_SEC: '120'

  # =========================
  # [工具路徑 / Node-ID 取得]
  # =========================
  TOOLS_PATH: /home/da40/charter/tools
  METRICS_TOOL: /home/da40/charter/tools/cpe_metrics_agent_serial.py
  NODE_ID_MAX_RETRIES: '10'
  NODE_ID_RETRY_INTERVAL_SEC: '3'
  NODE_ID_FALLBACK_CPE_INFO: '1'
  CPE_INFO_TOOL: './cpe_info'

  # =========================
  # [CPE Console / Serial]
  # =========================
  CPE_BAUD: '115200'
  CPE_USER: root
  CPE_PASSWORD: ''

  # =========================
  # [NOC / Cloud API]
  # - 建議用 profiles.json：NOC_PROFILE + PROFILES_FILE
  # - 若未提供 profiles，則使用 NOC_BASE/NOC_EMAIL/NOC_PASSWORD
  # =========================
  CUSTOMER_ID: '682d4e5179b80027cd6fb27e'
  NOC_PROFILE: SPECTRUM_INT
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
  NOC_BASE: https://piranha-int.tau.dev-charter.net
  NOC_EMAIL: ''
  NOC_PASSWORD: ''
  BEARER: 0
  INSECURE: 0

  # =========================
  # [Warehouse Page - Domain Name Entry]
  # - 預設只驗證 MyRouter（.lan 可選，見下方 env）
  #   http://MyRouter/warehouse     -> https://myrouter/cgi-bin/warehouse.cgi
  #   (optional) http://MyRouter.lan/warehouse -> https://myrouter.lan/cgi-bin/warehouse.cgi
  # =========================
  WAREHOUSE_HTTP_URLS: 'http://MyRouter/warehouse'
  # NOTE: device redirects http->https to /warehouse first, then serves the page at /warehouse/
  #       Example:
  #         http://MyRouter/warehouse -> 308 Location: https://myrouter/warehouse
  #         (follow) -> https://myrouter/warehouse/
  WAREHOUSE_EXPECT_HTTPS_URLS: 'https://myrouter/warehouse'
  # 主要用哪個 HTTPS URL 來抓表格（建議直接打 warehouse.cgi，解析表格最穩）
  PRIMARY_WAREHOUSE_HTTPS_URL: 'https://myrouter/cgi-bin/warehouse.cgi'

  WAREHOUSE_TOOL: /home/da40/charter/tools/cpe_warehouse_info.py
  WAREHOUSE_ID: 'ThylacineGone'
  WAREHOUSE_PASSWORD: '<fill>'
  WAREHOUSE_TIMEOUT_SEC: '3'
  WAREHOUSE_RETRIES: '15'
  WAREHOUSE_SLEEP_SEC: '5'

  # Redirect 檢查模式：
  # - strict   : Location 必須等於 expected (允許最後多 '/'，也允許相對路徑補全)
  # - prefix   : Location 只要以 expected 為 prefix
  # - https_only: 只要 Location 是 https://
  REDIRECT_MATCH_MODE: strict
  ALLOW_RELATIVE_LOCATION: '1'
  CHECK_HTTP_REDIRECT: '1'
  RECHECK_REDIRECT_AFTER_WIFI: '1'

  # follow redirects and validate final url_effective equals expected
  REDIRECT_CHECK_FINAL: '1'
  REDIRECT_FINAL_TIMEOUT_SEC: '12'

  # Redirect check retry (helpful right after factory reset)
  REDIRECT_RETRIES: '15'
  REDIRECT_SLEEP_SEC: '5'

  # =========================
  # [Domain Resolve]
  # - CHECK_DOMAIN_RESOLVE=1：會先解析 MyRouter / MyRouter.lan 的 IPv4
  # - EXPECTED_LAN_IP：期望解析到哪個 LAN IP（多數情境是 192.168.1.1）
  # =========================
  CHECK_DOMAIN_RESOLVE: '1'
  EXPECTED_LAN_IP: '192.168.1.1'
  DOMAIN_RESOLVE_STRICT: '1'
  # Resolve retry (helpful when name resolution/DNS is not ready right after factory reset)
  DOMAIN_RESOLVE_RETRIES: '10'
  DOMAIN_RESOLVE_SLEEP_SEC: '3'

  # =========================
  # [SSH enable + MAC Validation]
  # - 若要依文件要求「MAC address should be validated against ifconfig -a」
  #   請啟用下列兩項：
  #     ENABLE_SSH_VIA_NOC=1        （透過 NOC kvConfigs 開啟 SSH）
  #     VALIDATE_MACS_VIA_SSH=1     （SSH 進 CPE 跑 ifconfig -a 比對 Warehouse 欄位）
  # - SSH_ENABLE_PASSWORD/SSH_PASSWORD 為 CPE SSH 密碼（SSHM sshAuthPasswd）
  # - SSH_HOST 預設取 EXPECTED_LAN_IP（多數是 192.168.1.1）
  # =========================
  ENABLE_SSH_VIA_NOC: '1'
  SSH_ENABLE_TIMEOUT_MIN: '30'
  # Default operator password (same as sshAuthPasswd). Change in customer env if needed.
  SSH_ENABLE_PASSWORD: <fill>
  # After enabling SSH via NOC, wait a bit for sshd to become ready (align with C15807240 behavior)
  SSH_ENABLE_WAIT_SEC: '30'

  VALIDATE_MACS_VIA_SSH: '1'
  MAC_VALIDATION_STRICT: '1'
  WAN_IFACES: 'br-wan'
  LAN_IFACES: 'br-home,BR_LAN,br-lan'
  # Allow swap tolerance if wifi1/wifi2 labels are reversed on some platforms
  ALLOW_WIFI5_WIFI6_SWAP: '1'
  # Optional: override iface preference order (comma-separated)
  WLAN5_IFACES: 'wifi1'
  WLAN6_IFACES: 'wifi2'
  SSH_HOST: ''
  SSH_USER: operator
  SSH_PASSWORD: <fill>
  SSH_TIMEOUT_SEC: '30'
  SSH_READY_RETRIES: '10'
  SSH_READY_SLEEP_SEC: '3'
  SSH_READY_TIMEOUT_SEC: '8'
  SSH_READY_CMD: 'echo ready'
  SSH_IFCONFIG_RETRIES: '3'
  SSH_IFCONFIG_SLEEP_SEC: '3'
  SSH_IFCONFIG_MAX_TIMEOUT_SEC: '60'

  # =========================
  # [Validation]
  # - REQUIRED_FIELDS：必備欄位（逗號分隔）；空字串表示只檢查「能 parse table」
  # - CHECK_DEFAULT_B64：Default SSID/Password 是否看起來像 Base64 且可 decode
  # - EXPECT_SAME_AS_DEFAULT：改 Wi-Fi 前 Current SSID/Password 是否應顯示 Same as default
  # =========================
  REQUIRED_FIELDS: 'Manufacturer,Model #,WAN MAC Address,LAN MAC Address,IPv4 Address,Default SSID,Default Password,Current SSID,Current Password'
  CHECK_DEFAULT_B64: '1'
  EXPECT_SAME_AS_DEFAULT: '1'

  # =========================
  # [Factory Reset]
  # =========================
  DO_FACTORY_RESET: '1'
  FR_SETTLE_WAIT_SEC: '120'

  # FR 後 mute console（避免 serial 被 background job 佔用）
  RESET_MUTE_SECS: '60'
  RESET_MUTE_WITH_LOCK: '1'
  CONSOLE_LOCK_TIMEOUT_SEC: '5'
  CONSOLE_LOCK_RETRY_TIMEOUT_SEC: '60'
  CONSOLE_LOCK_RETRY_INTERVAL_SEC: '3'

  # （舊版相容）
  FACTORY_RESET_MUTE_SECS: ''
  FACTORY_RESET_MUTE_WITH_LOCK: '0'
  FACTORY_RESET_MUTE_LOCK_TIMEOUT_SEC: '5'

  # =========================
  # [Change Wi-Fi]
  # =========================
  CHANGE_WIFI: '1'
  NEW_WIFI_SSID: 'QA_Auto_SSID'
  NEW_WIFI_PASSWORD: '<fill>'
  WIFI_APPLY_WAIT_SEC: '60'

  # =========================
  # [Other]
  # =========================

  # MAC validation SSH retry rounds
  MAC_VALIDATE_ROUNDS: '3'
  MAC_VALIDATE_ROUND_BACKOFF_SEC: '10'
```bash
RID=1234
curl -sS "$CHARTER_BASE/api/runs/$RID/log" > run_${RID}_log.json

# 若 fail-hook 有產生 cpe logs
curl -sS "$CHARTER_BASE/api/runs/$RID/log-archives" | python3 -m json.tool
curl -fsSL "$CHARTER_BASE/api/runs/$RID/log-archive" -o run_${RID}_cpe_log.tar.gz
```

## 清理（Cleanup）


??? note "清理（Cleanup）— 點開看指令"
    ```bash
    # 清理已完成的 runs + workdir（避免磁碟累積）
    curl -sS -X DELETE "$CHARTER_BASE/api/runs/purge?older_than_days=0" | python3 -m json.tool
    ```

## 常見失敗與排除
- `noc-context timeout`：NOC endpoint 超時 → 增加 retry/backoff、確認出口網路/DNS
- eventual consistency：API 200 但 CPE 狀態未同步 → 用 wait/poll 再 assert
