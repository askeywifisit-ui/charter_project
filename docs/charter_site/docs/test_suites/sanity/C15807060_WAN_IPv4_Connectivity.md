# C15807060_WAN_IPv4_Connectivity

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_131=47` / `11F_140=5092`
- 風險等級（對 DUT 影響）：**HIGH**

## 目的（Purpose）
驗證 WAN IPv4 連通性（對外連線/連網狀態）。

## 前置條件（Preconditions）
- CPE/Cloud 需可連線（Internet/Cloud Connected）
- 需要的工具：`/home/da40/charter/tools`

## 測試行為摘要（What it does）
- 檢查 Internet/Cloud Connected
- ping/連線測試（IPv4）

## 主要參數（manifest env 重要值）
- CYCLES: `1`
- INTERVAL: `70`
- STOP_ON_FAIL: `0`

### 需依環境替換（給外部單位）
請參考 **Environment Template**，常見需替換：
- `TOOLS_PATH` / `PROFILES_FILE` / `NOC_PROFILE` / `CUSTOMER_ID`
- `CPE_HOST` / `LAN_PARENT_IFACE` / `WIFI_IFACE` / `PING_IFACE`

## manifest.yaml（節錄）
```yaml
name: C15807060_WAN_IPv4_Connectivity
version: v1-Internet_connectivity
suite: sanity
entrypoint: cycle_wrapper.py:run
entry: cycle_wrapper.py:run
env:
  CYCLES: '1'
  CYCLE_INTERVAL: '70'
  STOP_ON_FAIL: '0'
  ORIGINAL_ENTRY: main_impl.py:run


  # =========================
  # [CPE Ready Check + PDU Reset]
  # - 第 1 個 cycle 前檢查 cpe_info -status
  # - 不 ready：retry 5 次，每次 3 秒；仍不行就 pdu reset，wait 120 秒再重檢
  # =========================
  CPE_READY_CHECK: '1'
  CPE_INFO_STATUS_CMD: 'cpe_info -status'
  CPE_READY_MAX_RETRIES: '5'
  CPE_READY_RETRY_INTERVAL_SEC: '3'
  CPE_READY_REQUIRE_CLOUD: '1'
  PDU_RESET_ON_NOT_READY: '1'
  PDU_RESET_SCRIPT: '/home/da40/charter/tools/pdu_outlet1.py'
  PDU_RESET_ACTION: reset
  PDU_RESET_WAIT_SEC: '120'
  PDU_RESET_TIMEOUT_SEC: '600'

  # =========================
  # [工具路徑]
  # - TOOLS_PATH：控制機（control PC）上 tools 目錄位置
  # - TOOLS_PYTHON：執行 tools 的 Python 指令（例如 python3）
  # =========================
  TOOLS_PATH: /home/da40/charter/tools
  TOOLS_PYTHON: python3
  WAN_IPV4_METHOD: ssh
  ENABLE_SSH_PRECOND: '1'
  SSH_PRECOND_CACHE_ENABLED: '1'
  SSH_PRECOND_CACHE_TTL_SEC: '600'

  # =========================
  # [CPE 連線與 NOC 設定]
  # - CPE_IP：CPE LAN 管理 IP（通常 192.168.1.1）
  # - SSH_USER/SSH_PASSWORD：登入 CPE 的帳密（若客戶環境不同需更改）
  # - CUSTOMER_ID：要查詢/綁定的客戶 ID（若此腳本有用到 NOC API）
  # - NOC_PROFILE/PROFILES_FILE：從 profiles 檔案讀取 NOC base/email/password
  # =========================
  CPE_IP: 192.168.1.1
  SSH_USER: operator
  SSH_PASSWORD: <fill>
  CUSTOMER_ID: '682d4e5179b80027cd6fb27e'
  NOC_PROFILE: SPECTRUM_INT
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json

  # =========================
  # [Console / Serial 設定]
  # - CPE_DEV/CPE_BAUD：Console 裝置與鮑率（依實驗室/客戶端調整）
  # - CPE_USER/CPE_PASSWORD：Console 登入帳密（若為空字串表示無密碼）
  # =========================
  CPE_BAUD: '115200'
  CPE_USER: root
  CPE_PASSWORD: ''
  CPE_IFACE: br-wan
  API_BASE: http://127.0.0.1:8080

  # =========================
  # [Timing（毫秒）]
  # - SERIAL_SETTLE_MS：開啟 serial 後等待穩定的時間
  # - STEP_WAIT_* / WAIT_AFTER_STEP*：每個步驟前後等待時間（避免太快造成判斷失準）
  # =========================
  SERIAL_SETTLE_MS: '800'
  STEP_WAIT_BEFORE_MS: '100'
  STEP_WAIT_AFTER_MS: '100'
  WAIT_AFTER_STEP1_MS: '200'
  WAIT_AFTER_STEP2_MS: '200'
  WAIT_AFTER_STEP3_MS: '1200'

  # =========================
  # [WAN IPv4 重試設定]
  # - WAN_IPV4_RETRIES：取得 WAN IPv4 的重試次數
  # - WAN_IPV4_WAIT_MS：每次重試間隔（毫秒）
  # =========================
  WAN_IPV4_RETRIES: '12'
  WAN_IPV4_WAIT_MS: '700'
  CPE_PING1: 8.8.8.8
  CPE_PING2: 1.1.1.1
  PING_METHOD: ssh
  SSH_PING_TIMEOUT_SEC: '15'
  SSH_PING_COUNT: '1'

  # =========================
  # [Metrics / Log 輸出]
  # - METRICS_METHOD：取得 metrics 的方式（例如 ssh）
  # - SSH_METRICS_TIMEOUT_SEC：metrics 指令 timeout（秒）
  # - SHOW_METRICS/ECHO_METRICS：是否在 log 顯示 metrics 摘要
  # - ECHO_MAX_LINES：最多輸出幾行摘要
  # - DEBUG_METRICS：更詳細 debug（通常僅在追查問題時開）
  # - CPE_INFO_BIN：查詢 CPE 基本資訊的工具路徑
  # =========================
  METRICS_METHOD: ssh
  SSH_METRICS_TIMEOUT_SEC: '25'
  RETRIES: '3'
  INTERVAL_SEC: '1'
  SHOW_METRICS: '1'
  ECHO_METRICS: '1'
  ECHO_MAX_LINES: '12'
  DEBUG_METRICS: '0'
  CPE_INFO_BIN: /home/da40/charter/tools/cpe_info

  # =========================
  # [Control PC（控制機）網路介面]
  # - PING_IFACE：控制機用哪個介面做路由/探測（例如 eno2）
  # =========================
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
