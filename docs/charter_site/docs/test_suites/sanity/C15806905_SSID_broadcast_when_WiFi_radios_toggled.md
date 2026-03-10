# C15806905_SSID_broadcast_when_WiFi_radios_toggled

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_131=45` / `11F_140(current)=5204`
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
- INTERVAL: `20`
- STOP_ON_FAIL: `1`

### 需依環境替換（給外部單位）
請參考 **Environment Template**，常見需替換：
- `TOOLS_PATH` / `PROFILES_FILE` / `NOC_PROFILE` / `CUSTOMER_ID`
- `CPE_HOST` / `LAN_PARENT_IFACE` / `WIFI_IFACE` / `PING_IFACE`

## manifest.yaml（節錄）
```yaml
name: C15806905_SSID_broadcast_when_WiFi_radios_toggled
version: v16_platform_hint_manifest_fallback_warn
suite: sanity
entrypoint: cycle_wrapper.py:run
entry: cycle_wrapper.py:run
env:
  # ===============================
  # Wrapper / 長跑流程控制（參考 C00000003/C00000001）
  # ===============================
  CYCLES: '1'
  CYCLE_INTERVAL: '20'
  STOP_ON_FAIL: '1'
  ORIGINAL_ENTRY: main_impl_orig.py:run

  # ===============================
  # Tools 路徑
  # ===============================
  TOOLS_PATH: /home/da40/charter/tools
  CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
  CPE_SSH_TOOL: /home/da40/charter/tools/cpe_ssh.py

  # ===============================
  # Precondition: ready node-id（參考 C00000003）
  # ===============================
  NODE_ID_READY_CHECK: '1'
  NODE_ID_MAX_RETRIES: '10'
  NODE_ID_RETRY_INTERVAL_SEC: '5'

  # ===============================
  # Wrapper 其他 precondition（本案例預設不啟用）
  # ===============================
  CPE_READY_CHECK: '1'
  CPE_INFO_STATUS_CMD: "cpe_info -status"
  CPE_READY_MAX_RETRIES: '10'
  CPE_READY_RETRY_INTERVAL_SEC: '3'
  CPE_READY_REQUIRE_CLOUD: '1'
  PDU_RESET_ON_NOT_READY: '1'
  PDU_RESET_ACTION: reset
  PDU_RESET_TIMEOUT_SEC: '120'
  PDU_RESET_WAIT_SEC: '120'
  POST_PDU_STABILIZE_SEC: '40'
  ENABLE_SSH_FLOW: '1'
  SSH_ACTION: enable
  REQUIRE_SSH_READY: '1'
  SSH_READY_RETRY: '40'
  SSH_READY_WAIT_SEC: '3'
  SSH_READY_CMD: health

  # ===============================
  # NOC profile (recommended)
  # ===============================
  NOC_BASE: https://piranha-int.tau.dev-charter.net
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
  NOC_PROFILE: SPECTRUM_INT
  CUSTOMER_ID: '682d4e5179b80027cd6fb27e'
  # Optional override (if you don't want profile)
  NOC_EMAIL: ''
  NOC_PASSWORD: ''
  BEARER: '1'
  INSECURE: '0'
  NOC_TIMEOUT_SEC: '30'
  NOC_RETRIES: '3'

  # ===============================
  # CPE SSH (LAN)
  # ===============================
  SSH_HOST_LAN: 192.168.1.1
  SSH_USER: operator
  SSH_PASSWORD: "<fill>"
  SSH_TIMEOUT_MIN: '120'
  CPE_USER: operator
  CPE_PASSWORD: '<fill>'
  CPE_SSH_TIMEOUT_SEC: '25'
  SSH_TOOL_TIMEOUT: '25'

  # ===============================
  # WiFi client
  # WIFI_IFACE is provided by systemd (charter-worker.service) on this platform
  # ===============================
  # WIFI_BAND optional: '', '2g', '5g'
  WIFI_BAND: ""
  WIFI_CRED_PREFER: "current"
  WIFI_DHCP_TIMEOUT_SEC: '35'

  # wifi_iwd.py connect timeout (iwctl timeout). Default wifi_iwd is 40s; increase for stability.
  WIFI_IWD_TIMEOUT_SEC: '90'
  # After enabling WiFi from disabled state, wait a bit before association to let beacons stabilize.
  WIFI_POST_ENABLE_GRACE_SEC: '6'
  # Robust connect loop
  WIFI_CONNECT_RETRIES: '3'
  WIFI_CONNECT_RETRY_WAIT_SEC: '3'
  WIFI_TAKEOVER_ON_RETRY: '1'
  # If band-preferred connect fails, allow fallback to any band (2.4/5/6) to avoid false failures.
  WIFI_FALLBACK_ANY_BAND: '1'

  # SSID/PSK：預設會從 CPE 透過 SSH 讀取（cpe_ssh.py --cmd wifi-creds，參考 C00000003）
  WIFI_SSID: ''
  # WIFI_PSK optional override (default: from CPE wifi-creds)
  WIFI_PSK: ''
  # WIFI_PSK_ENV optional: read PSK from another env name
  WIFI_PSK_ENV: ''

  # 防止 WiFi 連線影響 main default route
  WIFI_NO_MAIN_DEFAULT: '1'
  WIFI_PBR_TABLE: '101'
  WIFI_PBR_FROM_IP: '0'

  # ===============================
  # waits/polls
  # ===============================
  WIFI_NOC_STATE_TIMEOUT_SEC: '180'
  WIFI_VIF_STATE_TIMEOUT_SEC: '180'
  WIFI_SCAN_TIMEOUT_SEC: '300'
  POLL_INTERVAL_SEC: '5'

  # Router-side VIF check after WiFi disable:
  # - default '0': if SSH reachability is lost (common when SSH is routed via the WiFi iface), skip this check and rely on client disconnect + scan absent.
  # - set '1' to strictly require SSH VIF OFF verification.
  REQUIRE_SSH_VIF_OFF: '0'

  # ===============================
  # checks
  # ===============================
  PING_TARGET: 192.168.1.1
  PING_COUNT: '2'
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
