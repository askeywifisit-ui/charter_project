# C15807944_Add_DHCP_Reservation

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_131=63` / `11F_140=5108`
- 風險等級（對 DUT 影響）：**HIGH**

## 目的（Purpose）
驗證新增 DHCP Reservation：雲端設定成功且 CPE 端 reserved/lease 表同步、LAN client 可拿到保留 IP。

## 前置條件（Preconditions）
- CPE/Cloud 需可連線（Internet/Cloud Connected）
- 需要的工具：`/home/da40/charter/tools`

## 測試行為摘要（What it does）
- （可選）清理既有 reservation
- 設定 reservation（NOC API）
- wait/poll CPE reserved/leased
- LAN renew + assert IP

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
name: C15807944_Add_DHCP_Reservation
version: v18-ipinuse-retry-cleanup
suite: sanity
entrypoint: cycle_wrapper.py:run
entry: cycle_wrapper.py:run
env:
  TEST_NAME: 'C15807944_Add_DHCP_Reservation'

  # Cycles (keep compatibility aliases for older runners)
  CYCLE_INTERVAL_SEC: '60'
  STOP_ON_FAIL: '1'
  CYCLES: '1'
  CYCLE_INTERVAL: '70'

  # Tools path
  TOOLS_PATH: '/home/da40/charter/tools'

  # Profiles / NOC (secrets live in PROFILES_FILE)
  NOC_PROFILE: 'SPECTRUM_INT'
  PROFILES_FILE: '/home/da40/charter/.secrets/noc_profiles.json'
  # Customer ID is required for NOC API endpoints in some INT environments.
  # You can also put customer_id into the selected profile inside PROFILES_FILE.
  CUSTOMER_ID: '682d4e5179b80027cd6fb27e'
  # Optional direct overrides (usually leave empty and use profile):
  # NOC_BASE: ''
  # NOC_CUSTOMER_ID: ''
  # NOC_EMAIL: ''
  # NOC_PASSWORD: ''
  # If your backend doesn't support /Customers/{cid}/nodes endpoints,
  # set the location ID explicitly to skip auto-resolution.
  # NOC_LOCATION_ID: ''

  # CPE access
  CPE_HOST: '192.168.1.1'
  CPE_SSH_USER: 'operator'
  SSH_PASSWORD: '<fill>'
  # SSH login / enable password should come from secrets/profile; not hard-coded here.
  # Supported env names (any one):
  #   - SSH_PASSWORD (preferred)
  #   - CPE_SSH_PASSWORD (login password override)
  #   - CPE_PASSWORD (legacy alias)
  SSH_READY_CMD: 'uptime'

  # SSH readiness / enable (v7-style)
  CPE_SSH_PORT: '22'
  # Default 30s to match platform expectation
  SSH_SCAN_TIMEOUT_SEC: '30'
  SSH_SCAN_INTERVAL_SEC: '2'
  CPE_SSH_TIMEOUT_SEC: '30'
  SSH_PASSWORD_DEFAULT: '<fill>'
  SSH_ENABLE_RETRIES: '2'
  WAIT_AFTER_SSH_ENABLE_SEC: '60'

  # PDU (only used if cloud not ready within timeout)
  POST_PDU_STABILIZE_SEC: '40'

  # Precondition timing
  CLOUD_READY_TIMEOUT_SEC: '30'
  CLOUD_READY_INTERVAL_SEC: '3'
  NODE_ID_MAX_RETRIES: '10'
  NODE_ID_RETRY_INTERVAL_SEC: '3'
  SSH_ENABLE_ATTEMPTS: '2'
  SSH_ENABLE_WAIT_SEC: '20'

  # LAN client for end-to-end DHCP renew
  # Use 'auto' to avoid interface-name collision on the control PC.
  # The tools/lan_macvlan.py will generate a unique ifname and return it in JSON.
  LAN_TEST_IFACE: 'auto'
  # Leave empty to auto-generate a unique locally-administered MAC per run.
  # You may still override this env to a fixed value if needed.
  LAN_TEST_MAC: ''
  LAN_PING_TARGET: 'google.com'
  LAN_RENEW_TIMEOUT_SEC: '120'

  # DHCP reservation test data
  TEST_HOSTNAME: 'lan_test0'
  TEST_RESERVED_IP: '192.168.1.225'
  # If TEST_RESERVED_IP is already reserved by another MAC, clear it first (best-effort)
  CLEAR_CONFLICTING_IP_RESERVATION: '1'
  # Clear all DHCP reservations in NOC for this location (best-effort).
  # WARNING: affects the entire location; use only in a dedicated lab location.
  CLEAR_ALL_NOC_DHCP_RESERVATIONS: '0'
  # If set, only delete reservations whose hostname starts with this prefix (e.g., 'lan_test'). Empty => delete all.
  CLEAR_ALL_NOC_DHCP_RESERVATIONS_HOSTNAME_PREFIX: 'lan_test'

  # If the preferred TEST_RESERVED_IP is already in use (reserved/leased) on the CPE, pick the next free IP in the same /24.
  AUTO_PICK_FREE_IP: '1'
  # When backend returns 422 "IP currently used", auto-try next IP(s) in same /24
  IP_IN_USE_RETRY_MAX: "10"
  # Best-effort cleanup: delete the reservation for this MAC before exit
  CLEANUP_AFTER_TEST: "1"


  # Lease visibility on CPE can lag behind DHCP renew; poll the leased table.
  DHCP_DUMP_RETRIES: '3'
  DHCP_DUMP_RETRY_WAIT_SEC: '2'
  LEASE_WAIT_TIMEOUT_SEC: '60'
  LEASE_WAIT_INTERVAL_SEC: '5'

  # After DHCP renew, leased table may update asynchronously
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
