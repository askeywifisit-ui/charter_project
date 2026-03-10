# C00000004_NOC_API_basic_test

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_131=43`
- 風險等級（對 DUT 影響）：**LOW**

## 目的（Purpose）
快速驗證 NOC API 基本可用（登入、取得必要 ID / 狀態）。

## manifest.yaml（節錄）
```yaml
name: C00000004_NOC_API_basic_test
version: v3-professional-noc_profile-only-nodeid-cpeinfo
suite: sanity
entrypoint: cycle_wrapper.py:run
entry: cycle_wrapper.py:run

env:
  ENABLE_HEALTH_WARNING: 1
  CYCLES: '1'
  CYCLE_INTERVAL: 70
  STOP_ON_FAIL: 1

  # cycle_wrapper 會依這個 entry 去找 module:func
  ORIGINAL_ENTRY: main_impl_orig.py:run

  # ---------- Tools 路徑 ----------
  TOOLS_PATH: /home/da40/charter/tools
  CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
  CPE_SSH_TOOL: /home/da40/charter/tools/cpe_ssh.py

  # node-id retry controls
  NODE_ID_MAX_RETRIES: 10
  NODE_ID_RETRY_INTERVAL_SEC: 5
  
  # ---------- Serial / CPE console ----------
  CPE_BAUD: 115200
  CPE_USER: root
  CPE_PASSWORD: null
  # 讓程式去 cpe_info 撈密碼

  # ---------- NOC / LOGIN INFO ----------
  NOC_BASE: https://piranha-int.tau.dev-charter.net
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
  CUSTOMER_ID: '682d4e5179b80027cd6fb27e'
  
  # ---------- SSH / Cloud SSH 配置----------
  SSH_USER: operator
  SSH_PASSWORD: "<fill>"
  SSH_TIMEOUT_MIN: 120
  SSH_REENABLE_EACH_CYCLE: 0
  SSH_HOST_LAN: 192.168.1.1
  WAN_SSH_REQUIRED: 0
  LAN_SSH_REQUIRED: 0

  SSH_TOOL_TIMEOUT: 15
  USE_CLOUD_SSH: "1"
  CPE_LOG_TIMEOUT_SEC: "240"
  NOC_PROFILE: SPECTRUM_INT

  # 控制只 enable / disable / both
  SSH_ACTION: enable

  # --- 新增：控制是否要跑 NOC API 測試 ---
  # 1 = 跑 get-location / speedtest / wifi / lte / reboot
  # 0 = 完全跳過，只做 SSH enable/disable
  ENABLE_NOC_API_TESTS: 1

  # --- speedtest / wifi / lte / reboot 測試開關與參數 ---
  SPEEDTEST_WAIT_SEC: 100
  ENABLE_SPEEDTEST: 1
  ENABLE_WIFI_TEST: 1
  ENABLE_LTE_TEST: 1
  ENABLE_SSH_FLOW: 0

  # reboot via NOC API , enable reboot must mute console 
  ENABLE_REBOOT_TEST: 0
  REBOOT_DELAY_SEC: 2

  # reboot 時 mute console 的秒數與 lock 機制 
  REBOOT_MUTE_SECS: 60
  REBOOT_MUTE_WITH_LOCK: 0

  # ---------- Precondition: CPE_READY ----------
  CPE_READY_CHECK: 1
  CPE_INFO_STATUS_CMD: "cpe_info -status"
  CPE_READY_MAX_RETRIES: 10
  CPE_READY_RETRY_INTERVAL_SEC: 3
  CPE_READY_REQUIRE_CLOUD: 1
  PDU_RESET_ON_NOT_READY: 1
  PDU_RESET_ACTION: reset
  PDU_RESET_TIMEOUT_SEC: 120
  PDU_RESET_WAIT_SEC: 120

  # ---------- Precondition: SSH_READY ----------
  REQUIRE_SSH_READY: 0
  SSH_READY_RETRY: 2
  SSH_READY_WAIT_SEC: 2
  SSH_READY_CMD: 'uptime'
  SPEEDTEST_MAX_TRIES: 3
  SPEEDTEST_INTERVAL_SEC: 10
  INTERNET_CHECK_MAX_RETRIES: '10'
  INTERNET_CHECK_INTERVAL_SEC: '3'

  # DNS 檢查（如果暫時不用，可以改成 ENABLE_DNS_CHECK: 0）
  ENABLE_DNS_CHECK: 0
  TARGET: www.google.com
  SECOND: cloudflare.com
  EXPECT_A_MIN: 1
  EXPECT_AAAA_MIN: 1
  RETRIES: 3
  INTERVAL_SEC: 3
  DNS_SSH_TIMEOUT_SEC: 30
  POST_PDU_STABILIZE_SEC: 40
```
