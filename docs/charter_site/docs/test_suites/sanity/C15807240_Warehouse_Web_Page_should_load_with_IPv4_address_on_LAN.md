# C15807240_Warehouse_Web_Page_should_load_with_IPv4_address_on_LAN

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_131=58` / `11F_140(current)=5205`
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
name: C15807240_Warehouse_Web_Page_should_load_with_IPv4_address_on_LAN
version: v3-warehouse-ipv4-lan-aliasfix2
suite: sanity
entrypoint: cycle_wrapper.py:run
entry: cycle_wrapper.py:run
env:
  # =========================
  # [Wrapper / 循環控制]
  # =========================
  CYCLES: '1'
  CYCLE_INTERVAL: '70'
  STOP_ON_FAIL: '1'
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
  # [Warehouse Page]
  # =========================
  WAREHOUSE_HTTP_URL: http://192.168.1.1/warehouse
  WAREHOUSE_HTTPS_URL: https://192.168.1.1/cgi-bin/warehouse.cgi
  WAREHOUSE_TOOL: /home/da40/charter/tools/cpe_warehouse_info.py
  WAREHOUSE_ID: 'ThylacineGone'
  WAREHOUSE_PASSWORD: '<fill>'
  WAREHOUSE_TIMEOUT_SEC: '3'
  WAREHOUSE_RETRIES: '10'
  WAREHOUSE_SLEEP_SEC: '3'
  CHECK_HTTP_REDIRECT: '1'

  # =========================
  # [Validation]
  # - REQUIRED_FIELDS：必備欄位（逗號分隔）；空字串表示只檢查「能 parse table」
  # - CHECK_DEFAULT_B64：Default SSID/Password 是否看起來像 Base64 且可 decode
  # - EXPECT_SAME_AS_DEFAULT：改 Wi-Fi 前 Current SSID/Password 是否應顯示 Same as default
  # =========================
  # 注意：不同韌體欄位名可能是 "IPv4 Address"（而非 "LAN IPv4 Address"）。
  REQUIRED_FIELDS: 'Manufacturer,Model #,WAN MAC Address,LAN MAC Address,IPv4 Address,Default SSID,Default Password,Current SSID,Current Password'
  CHECK_DEFAULT_B64: '1'
  EXPECT_SAME_AS_DEFAULT: '1'

  # =========================
  # [MAC Validation via SSH]
  # - VALIDATE_MACS：是否要用 SSH 抓 ifconfig -a 來驗證 warehouse 上的 MAC 欄位
  # - SSH_ENABLE_VIA_NOC：是否先透過 NOC API ssh_enable 設定密碼/timeout
  # - SSH_PASSWORD：登入 operator 的密碼（同時也會送給 NOC ssh_enable）
  # - *_IFACES：不同韌體介面名稱可能不同，允許用逗號列出候選
  # - MAC_PICK_PREFER_MATCH：若候選介面有多個存在，是否優先挑「MAC 與 warehouse 一致」的介面（建議 1）
  # =========================
  VALIDATE_MACS: '1'
  SSH_ENABLE_VIA_NOC: '1'
  SSH_TIMEOUT_MIN: '30'
  SSH_ENABLE_WAIT_SEC: '10'
  SSH_HOST: '192.168.1.1'
  SSH_USER: 'operator'
  SSH_PASSWORD: '<fill>'
  SSH_CMD_TIMEOUT_SEC: '10'
  SSH_RETRIES: '10'
  SSH_RETRY_INTERVAL_SEC: '3'
  SSH_BIND_SRC: ''
  MAC_PICK_PREFER_MATCH: '1'
  WAN_IFACES: 'br-wan'
  LAN_IFACES: 'br-home,BR_LAN,br-lan'
  WLAN24_IFACES: 'wifi0,home-ap-24,wlan0'
  # 部分機型 wifi1/wifi2 會在 5G/6G 間對調；建議保持兩者都在清單內並開啟 MAC_PICK_PREFER_MATCH
  WLAN5_IFACES: 'wifi1,wifi2,home-ap-50,wlan1'
  WLAN6_IFACES: 'wifi2,wifi1,home-ap-60,wlan2'

  # =========================
  # [Factory Reset]
  # - DO_FACTORY_RESET：是否執行 Factory Reset（0/1）
  # - FR_SETTLE_WAIT_SEC：FR 後先固定等待（秒），再開始抓 warehouse page
  DO_FACTORY_RESET: '1'
  FR_SETTLE_WAIT_SEC: '120'
  # - RESET_MUTE_SECS：FR 送出後，CPE 會 reboot；mute console 一段時間（避免背景程序碰 serial / console lock）
  # - RESET_MUTE_WITH_LOCK：mute 時是否先拿 serial lock（0/1）
  # - CONSOLE_LOCK_TIMEOUT_SEC：拿 lock 最久等待秒數
  # - CONSOLE_LOCK_RETRY_TIMEOUT_SEC：拿不到 lock 時，總重試時間（秒）
  # - CONSOLE_LOCK_RETRY_INTERVAL_SEC：每次重試間隔（秒）
  # （相容舊版）FACTORY_RESET_MUTE_SECS/FR_MUTE_SECS 仍可用
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
  # - CHANGE_WIFI：是否要改 SSID/Password（0/1）
  # - NEW_WIFI_SSID/NEW_WIFI_PASSWORD：要設定的新 SSID/密碼
  # - WIFI_APPLY_WAIT_SEC：送出更新後，等待設備同步的秒數
  # =========================
  CHANGE_WIFI: '1'
  NEW_WIFI_SSID: 'QA_Auto_SSID'
  NEW_WIFI_PASSWORD: '<fill>'
  WIFI_APPLY_WAIT_SEC: '60'

  # =========================
  # [Other]
  # =========================
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
