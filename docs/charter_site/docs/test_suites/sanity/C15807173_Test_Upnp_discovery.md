# C15807173_Test_Upnp_discovery

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_131=57` / `11F_140=5102`
- 風險等級（對 DUT 影響）：**MEDIUM**

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
- INTERVAL: `30`
- STOP_ON_FAIL: `1`

### 需依環境替換（給外部單位）
請參考 **Environment Template**，常見需替換：
- `TOOLS_PATH` / `PROFILES_FILE` / `NOC_PROFILE` / `CUSTOMER_ID`
- `CPE_HOST` / `LAN_PARENT_IFACE` / `WIFI_IFACE` / `PING_IFACE`

## manifest.yaml（節錄）
```yaml
name: C15807173_Test_Upnp_discovery
version: v1
suite: sanity
entrypoint: cycle_wrapper.py:run
entry: cycle_wrapper.py:run
env:
  # wrapper
  CYCLES: '1'
  CYCLE_INTERVAL: '30'
  STOP_ON_FAIL: 1
  ORIGINAL_ENTRY: main_impl_orig.py:run

  # tools
  TOOLS_PATH: /home/da40/charter/tools
  METRICS_TOOL: /home/da40/charter/tools/cpe_metrics_agent_serial.py
  CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
  CPE_SSH_TOOL: /home/da40/charter/tools/cpe_ssh.py

  # serial (not used by default; this case is SSH-only)
  USE_SERIAL_NODEID: '0'
  CPE_BAUD: 115200
  CPE_USER: root
  CPE_PASSWORD: null

  # NOC / LOGIN INFO (ref: C00000001)
  NOC_BASE: https://piranha-int.tau.dev-charter.net
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
  NOC_PROFILE: SPECTRUM_INT
  CUSTOMER_ID: '682d4e5179b80027cd6fb27e'

  # (optional) direct creds override; usually empty when using noc_profiles.json
  NOC_EMAIL: ''
  NOC_PASSWORD: ''

  # flags
  NOC_BEARER: '0'
  NOC_INSECURE: '0'

  # CPE LAN
  SSH_HOST_LAN: 192.168.1.1
  SSH_USER: operator
  SSH_PASSWORD: '<fill>'
  SSH_TOOL_TIMEOUT: 20
  SSH_ENABLE_AT_START: '1'
  SSH_TIMEOUT_MIN: '120'

  # SSH port wait (ref: C24532530)
  SSH_PORT_MAX_RETRIES: '10'
  SSH_PORT_INTERVAL_SEC: '3'
  SSH_PORT_CHECK_TIMEOUT: '3'
  SSH_PORT_TIMEOUT_SEC: '240'  # legacy overall timeout; kept for compatibility

  # LAN client (controlpc)
  LAN_IFACE: eno2

  # UPnP toggle
  UPNP_ENABLE_AT_START: '1'
  UPNP_DISABLE_AT_END: '1'
  UPNP_APPLY_WAIT_SEC: '40'
  MINIUPNPD_RETRIES: '5'
  MINIUPNPD_RETRY_INTERVAL_SEC: '3'
  MINIUPNPD_STOP_RETRIES: '10'
  MINIUPNPD_STOP_RETRY_INTERVAL_SEC: '3'

  # Reboot handling (UPnP enable/disable may reboot CPE)
  EXPECT_REBOOT_AFTER_UPNP_ENABLE: '1'
  EXPECT_REBOOT_AFTER_UPNP_DISABLE: '1'
  REBOOT_MUTE_SECS: '120'
  REBOOT_MUTE_WITH_LOCK: '1'
  SERIAL_MUTE_TOOL: /home/da40/charter/tools/serial_mute.py

  # cpe_info --status 在 reboot/boot 期間可能會卡住，拉長單次 timeout
  CPE_INFO_STATUS_TIMEOUT_SEC: '40'

  # CPE ready check (via cpe_info)
  CPE_READY_CHECK: '1'
  CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
  CPE_READY_MAX_RETRIES: '20'
  CPE_READY_RETRY_INTERVAL_SEC: '6'
  CPE_READY_REQUIRE_CLOUD: '1'

  # Process check
  MINIUPNPD_CMD: "ps | grep miniupnpd"

  # IGD discovery check (use tools/upnp_igd_tester.py)
  UPNP_IGD_TESTER: /home/da40/charter/tools/upnp_igd_tester.py
  UPNP_IGD_TIMEOUT_SEC: '60'
  UPNP_IGD_TEST_PORT: '54321'
  UPNP_IGD_PROTOCOL: 'TCP'

  # SSDP verification (prefer M-SEARCH; more stable than alive/byebye notify)
  REQUIRE_SSDP_MSEARCH_ON: '1'
  REQUIRE_SSDP_MSEARCH_OFF: '1'
  SSDP_MSEARCH_TIMEOUT_SEC: '3'
  SSDP_MSEARCH_RETRIES: '3'
  SSDP_MSEARCH_RETRY_SLEEP_SEC: '3'

  # (legacy) tcpdump capture (SSDP notify)
  REQUIRE_SSDP_ALIVE: '0'
  REQUIRE_SSDP_BYEBYE: '0'
  TCPDUMP_TIMEOUT_ON_SEC: '180'
  TCPDUMP_TIMEOUT_OFF_SEC: '180'
  TCPDUMP_RETRIES: '3'
  TCPDUMP_RETRY_SLEEP_SEC: '10'
  TCPDUMP_FILTER: "udp port 1900"
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
