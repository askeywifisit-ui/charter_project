# C15807139_SSH_should_be_allowed_to_WAN_from_operator_facing_client

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_131=56` / `11F_140=5101`
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
name: C15807139_SSH_should_be_allowed_to_WAN_from_operator_facing_client
version: v8
suite: sanity
entrypoint: cycle_wrapper.py:run
entry: cycle_wrapper.py:run
env:
  IPV4_TO_IPV6_SLEEP_SEC: 3
  CYCLES: '1'
  CYCLE_INTERVAL: '70'
  STOP_ON_FAIL: 1
  ORIGINAL_ENTRY: main_impl_orig.py:run
  TOOLS_PATH: /home/da40/charter/tools
  CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
  CPE_SSH_TOOL: /home/da40/charter/tools/cpe_ssh.py
  NODE_ID_USE_SERIAL: 0
  CUSTOMER_ID: 682d4e5179b80027cd6fb27e
  NOC_PROFILE: SPECTRUM_INT
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
  SSH_USER: operator
  SSH_PASSWORD: '<fill>'
  SSH_TIMEOUT_MIN: 120
  SSH_HOST_LAN: 192.168.1.1
  AUTO_SSH_ENABLE: 1
  REQUIRE_SSH_READY: 1
  SSH_ENABLE_ATTEMPTS: 2
  SSH_READY_WAIT_SEC: 30
  SSH_TOOL_TIMEOUT: 15
  ENABLE_SSH_FLOW: 1
  LAN_SSH_REQUIRED: 1
  WAN_SSH_TIMEOUT_SEC: 30
  SSH_ENABLE_WAIT_SEC: 10
  WAN_SSH_READY_RETRIES: 10
  WAN_SSH_READY_INTERVAL_SEC: 3
  WAN_SSH_READY_TIMEOUT_SEC: 3
  WAN_SSH_LOGIN_RETRIES: 8
  WAN_SSH_LOGIN_INTERVAL_SEC: 5
  WAN_SSH_LOGIN_TIMEOUT_SEC: 10
  ENABLE_IPV6: auto
  IPV6_REQUIRED: 1
  SKIP_IPV6: 0
  CPE_LAN_IFACE: br-home
  CLIENT_WAN_IFACE: auto
  CLIENT_LAN_IFACE: auto
  WAN_SSH_BIND_SRC4: auto
  WAN_SSH_BIND_SRC6: auto
  WAN_SSH_BIND_IFACE: auto
  REQUIRE_OPERATOR_FACING: 0
  CPE_READY_CHECK: '1'
  CPE_INFO_STATUS_CMD: cpe_info -status
  CPE_READY_MAX_RETRIES: '5'
  CPE_READY_RETRY_INTERVAL_SEC: '3'
  CPE_READY_REQUIRE_CLOUD: '1'
  PDU_RESET_ON_NOT_READY: '1'
  PDU_RESET_ACTION: reset
  PDU_RESET_WAIT_SEC: '120'
  CPE_READY_TIMEOUT_SEC: '60'
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
