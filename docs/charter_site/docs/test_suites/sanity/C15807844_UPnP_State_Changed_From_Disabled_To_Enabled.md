# C15807844_UPnP_State_Changed_From_Disabled_To_Enabled

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_131=61` / `11F_140=5183`
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
name: C15807844_UPnP_State_Changed_From_Disabled_To_Enabled
version: v5
suite: sanity
entrypoint: cycle_wrapper.py:run
entry: cycle_wrapper.py:run
env:
  CYCLES: '1'
  CYCLE_INTERVAL: '70'
  STOP_ON_FAIL: 1
  ORIGINAL_ENTRY: main_impl_orig.py:run_verify_upnp
  TOOLS_PATH: /home/da40/charter/tools
  METRICS_TOOL: /home/da40/charter/tools/cpe_metrics_agent_serial.py
  NODE_ID_MAX_RETRIES: 10
  NODE_ID_RETRY_INTERVAL_SEC: 2
  CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
  CPE_SSH_TOOL: /home/da40/charter/tools/cpe_ssh.py
  CPE_BAUD: 115200
  CPE_USER: root
  CPE_PASSWORD: null
  NOC_BASE: https://piranha-int.tau.dev-charter.net
  NOC_EMAIL: <fill>
  NOC_PASSWORD: <fill>
  CUSTOMER_ID: 682d4e5179b80027cd6fb27e
  NOC_PROFILE: SPECTRUM_INT
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
  SSH_USER: operator
  SSH_PASSWORD: <fill>
  SSH_TIMEOUT_MIN: 120
  SSH_REENABLE_EACH_CYCLE: 0
  SSH_HOST_LAN: 192.168.1.1
  WAN_SSH_REQUIRED: 1
  LAN_SSH_REQUIRED: 1
  SSH_TOOL_TIMEOUT: 15
  USE_CLOUD_SSH: '1'
  CPE_LOG_TIMEOUT_SEC: '240'
  SSH_ACTION: enable
  ENABLE_NOC_API_TESTS: 1
  SPEEDTEST_WAIT_SEC: 60
  ENABLE_SPEEDTEST: 1
  ENABLE_WIFI_TEST: 0
  ENABLE_LTE_TEST: 0
  ENABLE_SSH_FLOW: 1
  SSH_RECOVER_ON_FAIL: 1
  SSH_RECOVER_WAIT_SEC: 2
  SSH_RECOVER_GRACE_SEC: 5
  UPNP_HEALTH_TIMEOUT_SEC: 180
  SPEEDTEST_MAX_TRIES: 3
  SPEEDTEST_INTERVAL_SEC: 10
  CPE_HEALTH_WAIT_SEC: '40'
  ENABLE_DNS_CHECK: 0
  TARGET: www.google.com
  SECOND: cloudflare.com
  EXPECT_A_MIN: 1
  EXPECT_AAAA_MIN: 1
  RETRIES: 3
  INTERVAL_SEC: 3
  DNS_SSH_TIMEOUT_SEC: 30
  UPNP_ITERATIONS: 1
  UPNP_LOG_GREP: upnp
  UPNP_LOG_LINES: 100
  UPNP_LOG_WINDOW_MIN: 5
  CPE_HOST: 192.168.1.1
  UPNP_APPLY_WAIT_SEC: 10
  UPNP_REBOOT_WAIT_SEC: 60
  INTERNET_STATUS_MAX_RETRIES: 20
  INTERNET_STATUS_INTERVAL_SEC: 3
  REBOOT_MUTE_SECS: 60
  REBOOT_MUTE_WITH_LOCK: 1
  ENABLE_UPNP_HEALTH: 1
  UPNP_RESTORE_BASELINE: 0
  SSH_PORT_MAX_RETRIES: 20
  SSH_PORT_INTERVAL_SEC: 3
  UPNP_POST_REBOOT_SSH_REARM: 1
  UPNP_POST_REBOOT_SSH_PORT_TIMEOUT_SEC: 300
  UPNP_POST_REBOOT_SSH_RETRY_ON_FAIL: 1
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
