# C15807946_Delete_DHCP_Reservation

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_131=65` / `11F_140=5110`
- 風險等級（對 DUT 影響）：**HIGH**

## 目的（Purpose）
驗證刪除 DHCP Reservation：雲端刪除成功且 CPE 端 reserved 表移除（含同步等待）。

## 前置條件（Preconditions）
- CPE/Cloud 需可連線（Internet/Cloud Connected）
- 需要的工具：`/home/da40/charter/tools`

## 測試行為摘要（What it does）
- 建立 baseline reservation
- 刪除 reservation（NOC API）
- wait/poll NOC list
- wait/poll CPE reserved
- （可選）LAN renew

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
name: C15807946_Delete_DHCP_Reservation
version: v1-precond-baseline-ipinuse-retry-customersafe
suite: sanity
entrypoint: cycle_wrapper.py:run
entry: cycle_wrapper.py:run
env:
  TEST_NAME: C15807946_Delete_DHCP_Reservation
  CYCLE_INTERVAL_SEC: '60'
  STOP_ON_FAIL: '1'
  CYCLES: '1'
  CYCLE_INTERVAL: '70'
  TOOLS_PATH: /home/da40/charter/tools
  NOC_PROFILE: SPECTRUM_INT
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
  CUSTOMER_ID: 682d4e5179b80027cd6fb27e
  CPE_HOST: 192.168.1.1
  CPE_SSH_USER: operator
  SSH_PASSWORD: <fill>
  SSH_READY_CMD: uptime
  CPE_SSH_PORT: '22'
  SSH_SCAN_TIMEOUT_SEC: '30'
  SSH_SCAN_INTERVAL_SEC: '2'
  CPE_SSH_TIMEOUT_SEC: '30'
  SSH_PASSWORD_DEFAULT: <fill>
  SSH_ENABLE_RETRIES: '2'
  WAIT_AFTER_SSH_ENABLE_SEC: '60'
  POST_PDU_STABILIZE_SEC: '40'
  SERIAL_MUTE_SEC: '60'
  CLOUD_READY_TIMEOUT_SEC: '30'
  CLOUD_READY_INTERVAL_SEC: '3'
  NODE_ID_MAX_RETRIES: '10'
  NODE_ID_RETRY_INTERVAL_SEC: '3'
  SSH_ENABLE_ATTEMPTS: '2'
  SSH_ENABLE_WAIT_SEC: '20'
  LAN_TEST_IFACE: auto
  LAN_TEST_MAC: ''
  LAN_PING_TARGET: google.com
  LAN_RENEW_TIMEOUT_SEC: '120'
  TEST_HOSTNAME: lan_test0
  TEST_RESERVED_IP: 192.168.1.225
  CLEAR_CONFLICTING_IP_RESERVATION: '1'
  CLEAR_ALL_NOC_DHCP_RESERVATIONS: '0'
  CLEAR_ALL_NOC_DHCP_RESERVATIONS_HOSTNAME_PREFIX: 'lan_test'
  AUTO_PICK_FREE_IP: '1'
  # When backend returns 422 "IP currently used", auto-try next IP(s) in same /24
  IP_IN_USE_RETRY_MAX: "10"
  DHCP_DUMP_RETRIES: '8'
  DHCP_DUMP_RETRY_WAIT_SEC: '5'
  LEASE_WAIT_TIMEOUT_SEC: '180'
  LEASE_WAIT_INTERVAL_SEC: '10'
  # NOTE(OPT): Extend delete verification timeout to tolerate NOC eventual consistency
  DELETE_VERIFY_TIMEOUT_SEC: '240'
  DELETE_VERIFY_INTERVAL_SEC: '10'
  EXPECT_NO_NOC_RESERVATIONS_AFTER_DELETE: '1'
  EXPECT_NO_CPE_RESERVATIONS_AFTER_DELETE: '1'
  LAN_RENEW_AFTER_DELETE: '1'
  LAN_RENEW_AFTER_DELETE_ATTEMPTS: '2'
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
