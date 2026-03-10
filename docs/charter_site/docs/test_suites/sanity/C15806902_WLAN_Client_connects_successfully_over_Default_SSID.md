# C15806902_WLAN_Client_connects_successfully_over_Default_SSID

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_131=44` / `11F_140=5089`
- 風險等級（對 DUT 影響）：**HIGH**

## 目的（Purpose）
Sanity 測試：驗證基本功能可用性。

## 前置條件（Preconditions）
- CPE/Cloud 需可連線（Internet/Cloud Connected）
- 需要的工具：`/home/da40/charter/tools`

## 測試行為摘要（What it does）
- 依腳本執行主要步驟並回報結果

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
name: C15806902_WLAN_Client_connects_successfully_over_Default_SSID
version: v9.4-force-ping4-ip
suite: sanity
entrypoint: cycle_wrapper.py:run
entry: cycle_wrapper.py:run
env:
  # ===============================
  # Cycle wrapper controls
  # ===============================
  CYCLES: '1'
  CYCLE_INTERVAL: "70"
  STOP_ON_FAIL: "1"
  ORIGINAL_ENTRY: main_impl_orig.py:run

  # ===============================
  # Precondition: Factory reset to defaults (cycle #1 only)
  # ===============================
  PRECOND_FACTORY_RESET: "1"
  FACTORY_RESET_WAIT_SEC: "90"
  FACTORY_RESET_MUTE_SECS: "60"

  AFTER_RESET_CPE_READY_MAX_RETRIES: "120"
  AFTER_RESET_CPE_READY_RETRY_INTERVAL_SEC: "5"
  PDU_RESET_ON_NOT_READY_AFTER_RESET: "1"

  # ===============================
  # Tools paths
  # ===============================
  TOOLS_PATH: "/home/da40/charter/tools"
  CPE_INFO_TOOL: "/home/da40/charter/tools/cpe_info"
  CPE_SSH_TOOL: "/home/da40/charter/tools/cpe_ssh.py"
  WIFI_IWD_TOOL: "/home/da40/charter/tools/wifi_iwd.py"
  WIFI_NM_TOOL: "/home/da40/charter/tools/wifi_nm.py"

  # ===============================
  # Node-id retry controls
  # ===============================
  NODE_ID_MAX_RETRIES: "10"
  NODE_ID_RETRY_INTERVAL_SEC: "5"

  # ===============================
  # NOC profile (recommended)
  # ===============================
  NOC_BASE: "https://piranha-int.tau.dev-charter.net"
  PROFILES_FILE: "/home/da40/charter/.secrets/noc_profiles.json"
  NOC_PROFILE: "SPECTRUM_INT"
  CUSTOMER_ID: "682d4e5179b80027cd6fb27e"

  # ===============================
  # CPE access over SSH (LAN)
  # ===============================
  SSH_HOST_LAN: "192.168.1.1"
  SSH_USER: "operator"
  SSH_PASSWORD: "<fill>"
  SSH_TOOL_TIMEOUT: "15"
  SSH_TIMEOUT_MIN: "120"

  # ===============================
  # Precondition: CPE_READY via cpe_info
  # ===============================
  CPE_READY_CHECK: "1"
  CPE_READY_MAX_RETRIES: "10"
  CPE_READY_RETRY_INTERVAL_SEC: "3"
  CPE_READY_REQUIRE_CLOUD: "1"
  PDU_RESET_ON_NOT_READY: "1"
  PDU_RESET_ACTION: "reset"
  PDU_RESET_TIMEOUT_SEC: "120"
  PDU_RESET_WAIT_SEC: "120"
  POST_PDU_STABILIZE_SEC: "40"

  # PDU control (lab default)

  # ===============================
  # Precondition: SSH_ENABLE/READY via NOC
  # ===============================
  ENABLE_SSH_FLOW: "1"
  SSH_ACTION: "enable"
  REQUIRE_SSH_READY: "1"
  # After factory-reset, SSH may take some time to become reachable.
  SSH_READY_RETRY: "20"
  SSH_READY_WAIT_SEC: "6"
  SSH_READY_INITIAL_WAIT_SEC: "20"
  SSH_READY_PORT_TIMEOUT_SEC: "5"
  SSH_READY_CMD: "uptime"

  # ===============================
  # Console password fallback (disabled)
  # ===============================
  CONSOLE_PASSWORD_FALLBACK: "0"

  # ===============================
  # Wi-Fi basic test parameters
  # WIFI_METHOD: auto | iwd | nm
  # WIFI_BAND: 2g | 5g | 6g | (empty for any)
  # WIFI_CRED_PREFER: current | default
  # ===============================
  # ===============================
  # Test profile
  #   lab      : IPv6 not required (most labs do not have IPv6)
  #   customer : IPv6 required
  # ===============================
  # NOTE(OPT): Force iwd to avoid NM pick_ap failure when NM is unmanaged
  WIFI_METHOD: "iwd"
  # iwd: after connect, wifi_iwd.py can optionally "restore" NetworkManager.
  # Some customer environments see IPv6 vanish due to NM race; set to 0 to keep NM stopped during Wi-Fi test.
  # NOTE(OPT): Keep NetworkManager stopped during Wi-Fi test to avoid race
  WIFI_IWD_RESTORE_NM: "0"
  # If restore is enabled, set Wi-Fi device unmanaged in NM (recommended)
  WIFI_IWD_UNMANAGED: "1"
  # If TEST_BANDS is set, script will test each band in order.
  TEST_BANDS: "5g"
  WIFI_BAND: ""  # kept for compatibility; ignored when TEST_BANDS is set
  WIFI_CRED_PREFER: "default"
  WIFI_TIMEOUT_SEC: "auto"
  WIFI_DHCP_TIMEOUT_SEC: "auto"
  WIFI_NM_RETRIES: "2"
  WIFI_DISCONNECT_ON_EXIT: "1"

  # IPv6 address check (required by customer test plan; labs may skip)
  # IPv6 address check: "auto" uses TEST_PROFILE (customer=>required, lab=>skip)
  # IPv6 address check: auto (customer required, lab optional) | 0 | 1
  WIFI_CHECK_IPV6: "auto"
  WIFI_IPV6_WAIT_SEC: "auto"
  WIFI_IPV6_POLL_SEC: "2"
  # IPv6 sysctl fix: auto -> enabled for customer profile
  WIFI_IPV6_SYSCTL_FIX: "auto"
  # accept_ra value to set when sysctl fix triggers (2 recommended)
  WIFI_IPV6_ACCEPT_RA: "2"
  WIFI_PING6_INTERNET: "0"
  WIFI_PING6_TARGET: ""

  # Connectivity checks
  WIFI_PING_ROUTER: "192.168.1.1"
  WIFI_PING_TARGET: "8.8.8.8"
  WIFI_PING_INTERNET: "1"
  WIFI_PING_COUNT: "3"
  WIFI_PING_TIMEOUT_SEC: "5"
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
