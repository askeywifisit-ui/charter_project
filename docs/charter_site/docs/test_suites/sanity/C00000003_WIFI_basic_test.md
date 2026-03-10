# C00000003_WIFI_basic_test

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_131=42` / `11F_140=5164`
- 風險等級（對 DUT 影響）：**HIGH**

## 目的（Purpose）
Wi‑Fi 基本連線測試：取得 SSID/PSK、連線、拿到 IPv4、ping router/Internet。

## 前置條件（Preconditions）
- CPE/Cloud 需可連線（Internet/Cloud Connected）
- 需要的工具：`/home/da40/charter/tools`

## 測試行為摘要（What it does）
- 讀取 Wi‑Fi creds（CPE）
- iwd/nm 連線
- 確認 IPv4
- ping router
- ping internet

## 主要參數（manifest env 重要值）
- CYCLES: `10`
- INTERVAL: `10`
- STOP_ON_FAIL: `1`

### 需依環境替換（給外部單位）
請參考 **Environment Template**，常見需替換：
- `TOOLS_PATH` / `PROFILES_FILE` / `NOC_PROFILE` / `CUSTOMER_ID`
- `CPE_HOST` / `LAN_PARENT_IFACE` / `WIFI_IFACE` / `PING_IFACE`

## manifest.yaml（節錄）
```yaml
name: C00000003_WIFI_basic_test
version: v2-noc-context-retry-timeout-tolerant
suite: sanity
entrypoint: cycle_wrapper.py:run
entry: cycle_wrapper.py:run
env:
  # ===============================
  # Cycle wrapper controls
  # ===============================
  CYCLES: '1'
  CYCLE_INTERVAL: '10'
  STOP_ON_FAIL: 1
  ORIGINAL_ENTRY: main_impl_orig.py:run

  # ===============================
  # Tools paths
  # ===============================
  TOOLS_PATH: /home/da40/charter/tools
  CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
  CPE_SSH_TOOL: /home/da40/charter/tools/cpe_ssh.py
  WIFI_IWD_TOOL: /home/da40/charter/tools/wifi_iwd.py
  WIFI_NM_TOOL: /home/da40/charter/tools/wifi_nm.py

  # ===============================
  # Node-id retry controls
  # ===============================
  NODE_ID_MAX_RETRIES: 10
  NODE_ID_RETRY_INTERVAL_SEC: 5

  # ===============================
  # NOC profile (recommended)
  # ===============================
  NOC_BASE: https://piranha-int.tau.dev-charter.net
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
  NOC_PROFILE: SPECTRUM_INT
  CUSTOMER_ID: '682d4e5179b80027cd6fb27e'

  # ===============================
  # CPE access over SSH (LAN)
  # ===============================
  SSH_HOST_LAN: 192.168.1.1
  SSH_USER: operator
  SSH_PASSWORD: <fill>
  SSH_TOOL_TIMEOUT: 15
  SSH_TIMEOUT_MIN: 120

  # ===============================
  # Precondition: CPE_READY via cpe_info
  # ===============================
  CPE_READY_CHECK: 1
  CPE_INFO_STATUS_CMD: "cpe_info -status"
  CPE_READY_MAX_RETRIES: 10
  CPE_READY_RETRY_INTERVAL_SEC: 3
  CPE_READY_REQUIRE_CLOUD: 1
  PDU_RESET_ON_NOT_READY: 1
  PDU_RESET_ACTION: reset
  PDU_RESET_TIMEOUT_SEC: 120
  PDU_RESET_WAIT_SEC: 120
  POST_PDU_STABILIZE_SEC: 40

  # PDU control (lab default)

  # ===============================
  # Precondition: SSH_ENABLE/READY via NOC
  # ===============================
  ENABLE_SSH_FLOW: 1
  SSH_ACTION: enable
  REQUIRE_SSH_READY: 1
  SSH_READY_RETRY: 2
  SSH_READY_WAIT_SEC: 2
  SSH_READY_CMD: uptime

  # ===============================
  # Wi-Fi basic test parameters
  # WIFI_METHOD: auto | iwd | nm
  # WIFI_BAND: 2g | 5g | 6g | (empty for any)
  # WIFI_CRED_PREFER: current | default
  # ===============================

  WIFI_METHOD: "auto"
  WIFI_BAND: "5g"
  WIFI_CRED_PREFER: "current"

  WIFI_TIMEOUT_SEC: "45"
  WIFI_NM_RETRIES: "2"
  WIFI_DISCONNECT_ON_EXIT: "1"


  # Connectivity checks
  WIFI_PING_ROUTER: 192.168.1.1
  WIFI_PING_TARGET: www.google.com
  WIFI_PING_INTERNET: 1
  WIFI_PING_COUNT: 3
  WIFI_PING_TIMEOUT_SEC: 5
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
