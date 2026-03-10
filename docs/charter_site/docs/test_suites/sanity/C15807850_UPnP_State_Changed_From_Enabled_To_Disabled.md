# C15807850_UPnP_State_Changed_From_Enabled_To_Disabled

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_131=62` / `11F_140=5184`
- 風險等級（對 DUT 影響）：**HIGH**

## 目的（Purpose）
驗證 UPnP discovery/功能：包含 enable/disable 與 M-SEARCH 驗證。

## 前置條件（Preconditions）
- CPE/Cloud 需可連線（Internet/Cloud Connected）
- 需要的工具：`/home/da40/charter/tools`

## 測試行為摘要（What it does）
- （可選）UPnP enable
- SSDP M-SEARCH 驗證 present/absent
- （可選）reboot/等待
- 收集 logpull（fail-hook）

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
name: C15807850_UPnP_State_Changed_From_Enabled_To_Disabled
version: v6
suite: sanity
entrypoint: cycle_wrapper.py:run
entry: cycle_wrapper.py:run
env:

  # =========================
  # [Wrapper / 迴圈控制]
  # - CYCLES：總共跑幾輪
  # - CYCLE_INTERVAL：每輪之間等待秒數
  # - STOP_ON_FAIL：遇到 fail 是否立刻停止（1=停止 / 0=不中斷）
  # - ORIGINAL_ENTRY：wrapper 內部實際呼叫的原始入口
  # =========================
  CYCLES: '1'
  CYCLE_INTERVAL: '70'
  STOP_ON_FAIL: 1
  ORIGINAL_ENTRY: main_impl_orig.py:run_verify_upnp_enabled_to_disabled

  # =========================
  # [工具路徑 / 指標收集]
  # - TOOLS_PATH：tools 目錄
  # - METRICS_TOOL：收集 CPE 指標工具
  # =========================
  TOOLS_PATH: /home/da40/charter/tools
  METRICS_TOOL: /home/da40/charter/tools/cpe_metrics_agent_serial.py

  # =========================
  # [Node ID / 啟動等待]
  # - NODE_ID_MAX_RETRIES：找不到 node_id 時最多重試次數
  # - NODE_ID_RETRY_INTERVAL_SEC：每次重試間隔秒數
  # =========================
  NODE_ID_MAX_RETRIES: 10
  NODE_ID_RETRY_INTERVAL_SEC: 2

  # =========================
  # [CPE 查詢 / SSH 工具]
  # - CPE_INFO_TOOL：查 CPE 狀態/版本/介面等資訊
  # - CPE_SSH_TOOL：透過 LAN/Cloud SSH 下指令的工具
  # =========================
  CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
  CPE_SSH_TOOL: /home/da40/charter/tools/cpe_ssh.py

  # =========================
  # [Console/Serial 連線]
  # - CPE_DEV/CPE_BAUD：Console/Serial 裝置與 baudrate
  # - CPE_USER/CPE_PASSWORD：登入帳密（null 代表由腳本自行處理/ fallback）
  # =========================
  CPE_BAUD: 115200
  CPE_USER: root
  CPE_PASSWORD: null

  # =========================
  # [NOC / Cloud API 與 Profile]
  # - NOC_BASE/NOC_EMAIL/NOC_PASSWORD：NOC API 登入資訊
  # - CUSTOMER_ID：要測的 customer/account id
  # - NOC_PROFILE/PROFILES_FILE：profiles 檔案選用
  # =========================
  NOC_BASE: https://piranha-int.tau.dev-charter.net
  NOC_EMAIL: <fill>
  NOC_PASSWORD: <fill>
  CUSTOMER_ID: '682d4e5179b80027cd6fb27e'
  NOC_PROFILE: SPECTRUM_INT
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json

  # =========================
  # [SSH 流程控制]
  # - SSH_USER/SSH_PASSWORD：SSH 登入帳密
  # - SSH_HOST_LAN：CPE LAN 管理 IP
  # - SSH_TIMEOUT_MIN：整體 SSH 流程上限（分鐘）
  # - WAN_SSH_REQUIRED/LAN_SSH_REQUIRED：是否要求 WAN/LAN SSH 必須可用
  # - USE_CLOUD_SSH：是否允許走 cloud-ssh
  # =========================
  SSH_USER: operator
  SSH_PASSWORD: <fill>
  SSH_TIMEOUT_MIN: 120
  SSH_REENABLE_EACH_CYCLE: 0
  SSH_HOST_LAN: 192.168.1.1
  WAN_SSH_REQUIRED: 1
  LAN_SSH_REQUIRED: 1
  SSH_TOOL_TIMEOUT: 15
  USE_CLOUD_SSH: '1'

  # =========================
  # [Log / Timeout]
  # - CPE_LOG_TIMEOUT_SEC：抓 CPE log timeout(秒)
  # =========================
  CPE_LOG_TIMEOUT_SEC: '240'

  # =========================
  # [測試動作 / 啟用開關]
  # - SSH_ACTION：本次要執行的動作（enable/disable/check 等）
  # - ENABLE_NOC_API_TESTS：是否啟用 NOC API 測試流程
  # =========================
  SSH_ACTION: enable
  ENABLE_NOC_API_TESTS: 1

  # =========================
  # [Speedtest 測項控制]
  # - ENABLE_SPEEDTEST：是否執行 speedtest
  # - SPEEDTEST_WAIT_SEC：speedtest 前後等待秒數
  # - ENABLE_WIFI_TEST/ENABLE_LTE_TEST：是否同時跑 Wi-Fi/LTE 測項
  # =========================
  SPEEDTEST_WAIT_SEC: 60
  ENABLE_SPEEDTEST: 1
  ENABLE_WIFI_TEST: 0
  ENABLE_LTE_TEST: 0

  # =========================
  # [SSH Recover / Re-arm（可選）]
  # - ENABLE_SSH_FLOW：是否啟用「確保 SSH 可用」流程（含 recover）
  # - SSH_RECOVER_*：失敗時的 recover 行為
  # =========================
  ENABLE_SSH_FLOW: 1
  SSH_RECOVER_ON_FAIL: 1
  SSH_RECOVER_WAIT_SEC: 2
  SSH_RECOVER_GRACE_SEC: 5

  # =========================
  # [UPnP 測試參數（Realize timeout）]
  # - UPNP_HEALTH_TIMEOUT_SEC：等待 modeRealized 的 timeout（秒）
  # =========================
  UPNP_HEALTH_TIMEOUT_SEC: 180

  # =========================
  # [Speedtest 測項控制（續）]
  # - SPEEDTEST_MAX_TRIES/SPEEDTEST_INTERVAL_SEC：speedtest 失敗重試/間隔
  # =========================
  SPEEDTEST_MAX_TRIES: 3
  SPEEDTEST_INTERVAL_SEC: 10

  # =========================
  # [健康檢查 / 等待（續）]
  # - CPE_HEALTH_WAIT_SEC：speedtest 後等待多久再做 health check
  # =========================
  CPE_HEALTH_WAIT_SEC: '40'

  # =========================
  # [DNS 檢查（可選）]
  # - ENABLE_DNS_CHECK：是否啟用 DNS resolve 檢查
  # - TARGET/SECOND：要解析的 domain
  # - EXPECT_A_MIN/EXPECT_AAAA_MIN：期望至少拿到幾筆 A/AAAA
  # - RETRIES/INTERVAL_SEC：重試次數與間隔秒數
  # =========================
  ENABLE_DNS_CHECK: 0
  TARGET: www.google.com
  SECOND: cloudflare.com
  EXPECT_A_MIN: 1
  EXPECT_AAAA_MIN: 1
  RETRIES: 3
  INTERVAL_SEC: 3
  DNS_SSH_TIMEOUT_SEC: 30

  # =========================
  # [UPnP 測試參數（續）]
  # - UPNP_ITERATIONS：UPnP enable/disable 動作的迭代次數
  # - UPNP_LOG_*：log 擷取的 grep/行數/時間窗
  # - UPNP_APPLY_WAIT_SEC：套用設定後等待秒數
  # - UPNP_REBOOT_WAIT_SEC：若觸發 reboot，等待秒數
  # - CPE_HOST：CPE 管理 IP（部分工具會用到）
  # =========================
  UPNP_ITERATIONS: 1
  UPNP_LOG_GREP: upnp
  UPNP_LOG_LINES: 100
  UPNP_LOG_WINDOW_MIN: 5
  CPE_HOST: 192.168.1.1
  UPNP_APPLY_WAIT_SEC: 10
  UPNP_REBOOT_WAIT_SEC: 60

  # =========================
  # [Internet 狀態確認]
  # - INTERNET_STATUS_MAX_RETRIES/INTERNET_STATUS_INTERVAL_SEC：Internet 狀態檢查重試/間隔
  # =========================
  INTERNET_STATUS_MAX_RETRIES: 20
  INTERNET_STATUS_INTERVAL_SEC: 3

  # =========================
  # [Reboot mute / Lock]
  # - REBOOT_MUTE_SECS：reboot 後 mute 秒數（避免誤判）
  # - REBOOT_MUTE_WITH_LOCK：1=使用 lock 檔避免並發互相干擾
  # =========================
  REBOOT_MUTE_SECS: 60
  REBOOT_MUTE_WITH_LOCK: 1

  # =========================
  # [UPnP Health / Baseline]
  # - ENABLE_UPNP_HEALTH：是否做 UPnP health check
  # - UPNP_RESTORE_BASELINE：是否在結束後還原 baseline
  # =========================
  ENABLE_UPNP_HEALTH: 1
  UPNP_RESTORE_BASELINE: 0

  # =========================
  # [SSH Port 檢查（連線就緒）]
  # - SSH_PORT_MAX_RETRIES/SSH_PORT_INTERVAL_SEC：檢查 port 22 ready 的重試/間隔
  # =========================
  SSH_PORT_MAX_RETRIES: 20
  SSH_PORT_INTERVAL_SEC: 3

  # =========================
  # [網路介面 / PDU（若測項包含斷電/外部控制）]
  # - PING_IFACE：control PC 用哪張網卡做 ping/路由（依環境）
  # - PDU_SCRIPT：控制 PDU 的腳本路徑（若需要斷電/上電）
  # - PDU_OUTLET_ID：PDU outlet 編號
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
