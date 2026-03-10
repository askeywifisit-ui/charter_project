# C15807947_Factory_Reset_DHCP_Reservation

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_131=66` / `11F_140=5111`
- 風險等級（對 DUT 影響）：**HIGH**

## 目的（Purpose）


## 前置條件（Preconditions）
- CPE/Cloud 需可連線（Internet/Cloud Connected）
- 需要的工具：`/home/da40/charter/tools`

## 測試行為摘要（What it does）


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
name: C15807947_Factory_Reset_DHCP_Reservation
version: v2-noc-dhcp-reserved-factoryreset-verify-serialmute-1
suite: sanity
entrypoint: cycle_wrapper.py:run
entry: cycle_wrapper.py:run
env:
  TEST_NAME: 'C15807947_Factory_Reset_DHCP_Reservation'

  # Cycles
  CYCLE_INTERVAL_SEC: '60'
  STOP_ON_FAIL: '1'

  # Tools path (tools.zip extracted/installed in runner)
  TOOLS_PATH: /home/da40/charter/tools

  # NOC profile (recommended) or direct creds below
  NOC_PROFILE: SPECTRUM_INT
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
  CUSTOMER_ID: '682d4e5179b80027cd6fb27e'

  # Direct NOC creds override (if not using profile)
  NOC_BASE: ''
  NOC_EMAIL: ''
  NOC_PASSWORD: ''

  # CPE SSH
  CPE_HOST: 192.168.1.1
  CPE_SSH_PORT: '22'
  CPE_SSH_USER: operator
  SSH_PASSWORD: '<fill>'
  SSH_READY_CMD: uptime
  SSH_SCAN_TIMEOUT_SEC: '60'
  SSH_SCAN_INTERVAL_SEC: '2'
  SSH_ENABLE_RETRIES: '2'
  SSH_ENABLE_WAIT_SEC: '60'
  SSH_ENABLE_TIMEOUT_MIN: '120'

  # Cloud readiness check
  CLOUD_READY_TIMEOUT_SEC: '30'
  CLOUD_READY_INTERVAL_SEC: '3'

  # DHCP reservation test data
  TEST_HOSTNAME: 'lan_test0'
  LAN_TEST_MAC: '02:11:22:33:44:55'
  TEST_RESERVED_IP: '192.168.1.222'

  # If TEST_RESERVED_IP is already reserved by another MAC:
  #   - pick_free: choose an unused IP from same /24 pool (default)
  #   - steal: delete the other MAC reservation then proceed with requested IP
  #   - fail: stop and report the conflict
  ON_IP_CONFLICT: 'pick_free'
  RESERVED_IP_POOL_START: '200'
  RESERVED_IP_POOL_END: '250'

  # CPE dhcp table dump
  DHCP_DUMP_RETRIES: '3'
  DHCP_DUMP_RETRY_WAIT_SEC: '2'

  # Wait for reserved entry to appear on CPE
  RESERVED_WAIT_TIMEOUT_SEC: '180'
  RESERVED_WAIT_INTERVAL_SEC: '5'
  RESERVED_REQUIRE_HOSTNAME: '0'

  # Factory reset + post-reset verification
  DO_FACTORY_RESET: '1'
  # Serial mute window (best-effort) to avoid any local serial agent touching /dev/ttyUSB* during reset/boot
  # Set to 0 to disable
  RESET_MUTE_SECS: '120'
  SERIAL_MUTE_STRICT: '0'

  # FACTORY_RESET_MODE:
  #   - full (default): full factory reset (all flags True)
  #   - network_only: only reset networkConfiguration
  #   - empty: send empty payload
  FACTORY_RESET_MODE: 'full'
  POST_RESET_CLOUD_TIMEOUT_SEC: '600'
  POST_RESET_CLOUD_INTERVAL_SEC: '5'
  POST_RESET_NO_RESV_TIMEOUT_SEC: '600'
  POST_RESET_NO_RESV_INTERVAL_SEC: '10'
  CYCLES: '1'
  CYCLE_INTERVAL: 70
  NODE_ID_MAX_RETRIES: 10
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
