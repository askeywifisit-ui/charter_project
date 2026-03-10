# C15807949_IP_reservation_for_WLAN_connected_clients

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_131=67` / `11F_140=5112`
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
- INTERVAL: `60`
- STOP_ON_FAIL: `1`

### 需依環境替換（給外部單位）
請參考 **Environment Template**，常見需替換：
- `TOOLS_PATH` / `PROFILES_FILE` / `NOC_PROFILE` / `CUSTOMER_ID`
- `CPE_HOST` / `LAN_PARENT_IFACE` / `WIFI_IFACE` / `PING_IFACE`

## manifest.yaml（節錄）
```yaml
name: C15807949_IP_reservation_for_WLAN_connected_clients
version: v1-wifi-noc-dhcp-resv-reconnect-delete-ssh-retry
suite: sanity
entrypoint: cycle_wrapper.py:run
entry: cycle_wrapper.py:run
env:
  TEST_NAME: 'C15807949_IP_reservation_for_WLAN_connected_clients'

  # ===============================
  # Cycle wrapper controls
  # ===============================
  CYCLE_INTERVAL_SEC: '60'
  STOP_ON_FAIL: '1'
  CYCLES: '1'
  CYCLE_INTERVAL: '70'
  ORIGINAL_ENTRY: 'main_impl.py:run'

  # ===============================
  # Tools paths
  # ===============================
  TOOLS_PATH: '/home/da40/charter/tools'
  WIFI_IWD_TOOL: '/home/da40/charter/tools/wifi_iwd.py'
  WIFI_NM_TOOL: '/home/da40/charter/tools/wifi_nm.py'

  # ===============================
  # Profiles / NOC (secrets live in PROFILES_FILE)
  # ===============================
  NOC_PROFILE: 'SPECTRUM_INT'
  PROFILES_FILE: '/home/da40/charter/.secrets/noc_profiles.json'
  CUSTOMER_ID: '682d4e5179b80027cd6fb27e'
  # Optional direct overrides (usually leave empty and use profile):
  # NOC_BASE: ''
  # NOC_CUSTOMER_ID: ''
  # NOC_EMAIL: ''
  # NOC_PASSWORD: ''
  # If your backend doesn't support /Customers/{cid}/nodes endpoints,
  # set the location ID explicitly to skip auto-resolution:
  # NOC_LOCATION_ID: ''

  # ===============================
  # CPE access (for wifi-creds and DHCP table dumps)
  # ===============================
  CPE_HOST: '192.168.1.1'
  CPE_SSH_USER: 'operator'
  SSH_PASSWORD: <fill>
  CPE_SSH_PORT: '22'
  CPE_SSH_TIMEOUT_SEC: '30'
  SSH_READY_CMD: 'uptime'

  # SSH readiness / enable (v7-style)
  SSH_SCAN_TIMEOUT_SEC: '30'
  SSH_SCAN_INTERVAL_SEC: '2'
  SSH_PASSWORD_DEFAULT: <fill>
  SSH_ENABLE_RETRIES: '2'
  WAIT_AFTER_SSH_ENABLE_SEC: '60'

  # ===============================
  # PDU (only used if cloud not ready within timeout)
  # ===============================
  POST_PDU_STABILIZE_SEC: '40'

  # Precondition timing
  CLOUD_READY_TIMEOUT_SEC: '30'
  CLOUD_READY_INTERVAL_SEC: '3'
  NODE_ID_MAX_RETRIES: '10'
  NODE_ID_RETRY_INTERVAL_SEC: '3'
  SSH_ENABLE_ATTEMPTS: '2'
  SSH_ENABLE_WAIT_SEC: '20'

  # ===============================
  # Wi-Fi client parameters (Control PC)
  # ===============================
  # WIFI_METHOD: auto | iwd | nm
  # NOTE(OPT): Force iwd-only to avoid NM pick_ap / unmanaged failures during reconnect
  WIFI_METHOD: 'iwd'
  # WIFI_BAND: 2g | 5g | 6g | (empty for any)
  WIFI_BAND: '5g'
  WIFI_CRED_PREFER: 'current'
  # NOTE(OPT): Slightly extend Wi-Fi connect timeout
  WIFI_TIMEOUT_SEC: '60'
  # NOTE(OPT): Disable NM retries (iwd-only)
  WIFI_NM_RETRIES: '0'
  WIFI_RECONNECT_WAIT_SEC: '5'
  WIFI_DISCONNECT_ON_EXIT: '1'

  # If your OS randomizes Wi-Fi MAC per connection/SSID, set these:
  WIFI_FORCE_STATIC_MAC: '0'
  WIFI_TEST_MAC: ''

  # Optional connectivity checks
  WIFI_PING_ROUTER_ENABLE: '1'
  WIFI_PING_ROUTER: '192.168.1.1'
  WIFI_PING_INTERNET: '0'
  WIFI_PING_TARGET: 'www.google.com'
  WIFI_PING_COUNT: '3'
  WIFI_PING_TIMEOUT_SEC: '5'

  # ===============================
  # DHCP reservation test data
  # ===============================
  TEST_HOSTNAME: 'wifi_test0'
  TEST_RESERVED_IP: '192.168.1.225'
  # Manual TP expects reserved IP differs from initial lease.
  # If you need to allow reserving the current IP, set to 1:
  ALLOW_SAME_IP: '0'

  # If TEST_RESERVED_IP is already reserved by another MAC, clear it first (best-effort)
  CLEAR_CONFLICTING_IP_RESERVATION: '1'

  # Clear all DHCP reservations in NOC for this location (best-effort).
  # WARNING: affects the entire location; use only in a dedicated lab location.
  CLEAR_ALL_NOC_DHCP_RESERVATIONS: '0'
  CLEAR_ALL_NOC_DHCP_RESERVATIONS_HOSTNAME_PREFIX: ''

  # If the preferred TEST_RESERVED_IP is already in use (reserved/leased) on the CPE,
  # or equals current lease, pick the next free IP in the same /24.
  AUTO_PICK_FREE_IP: '1'

  WAIT_AFTER_RESERVATION_SET_SEC: '5'

  # Delete + verify removal
  DELETE_RESERVATION_AT_END: '1'
  CLEANUP_ON_FAIL: '1'
  RESERVED_ABSENT_TIMEOUT_SEC: '60'
  RESERVED_ABSENT_INTERVAL_SEC: '5'

  # DHCP dump robustness
  DHCP_DUMP_RETRIES: '3'
  DHCP_DUMP_RETRY_WAIT_SEC: '2'
  LEASE_WAIT_TIMEOUT_SEC: '60'
  LEASE_WAIT_INTERVAL_SEC: '5'
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

- **HTTP 422（reservation set）不一定是 MAC 問題**：可能是指定的 `TEST_RESERVED_IP` 已被其他裝置使用（例如訊息出現 *used by Netgear*）。
- **專業做法：定義保留 IP 區**：建議把 DHCP reservation 固定在 `192.168.1.240~249`（避免與一般 DHCP lease 撞 IP）。
  - 推薦預設：`TEST_RESERVED_IP=192.168.1.240`
  - 如仍可能撞到：啟用 `AUTO_PICK_FREE_IP=1`（在保留區內自動挑可用 IP）。


- `noc-context timeout`：NOC endpoint 超時 → 增加 retry/backoff、確認出口網路/DNS
- eventual consistency：API 200 但 CPE 狀態未同步 → 用 wait/poll 再 assert
