# C15807061_WAN_IPv6_Connectivity

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_131=48` / `11F_140=5170`
- 風險等級（對 DUT 影響）：**HIGH**

## 目的（Purpose）
驗證 WAN IPv6 連通性（對外連線/連網狀態）。

## 前置條件（Preconditions）
- CPE/Cloud 需可連線（Internet/Cloud Connected）
- 需要的工具：`/home/da40/charter/tools`

## 測試行為摘要（What it does）
- 檢查 Internet/Cloud Connected
- ping/連線測試（IPv6）

## 主要參數（manifest env 重要值）
- CYCLES: `'1'# 循環次數（整數 >=1）`
- INTERVAL: `'60'# 每次循環間隔（秒）`
- STOP_ON_FAIL: `'0'         # 0=失敗繼續；1=失敗即停`

### 需依環境替換（給外部單位）
請參考 **Environment Template**，常見需替換：
- `TOOLS_PATH` / `PROFILES_FILE` / `NOC_PROFILE` / `CUSTOMER_ID`
- `CPE_HOST` / `LAN_PARENT_IFACE` / `WIFI_IFACE` / `PING_IFACE`

## manifest.yaml（節錄）
```yaml
name: C15807061_WAN_IPv6_Connectivity
version: v1-WAN_IPv6_Connectivity
suite: sanity
entrypoint: cycle_wrapper.py:run
entry: cycle_wrapper.py:run
env:
  SERIAL_DIAG_ENABLED: '0'  # 0=預設不跑 serial diag；1=啟用
  SKIP_ON_NO_IPV6: '0'  # 1=無 IPv6 則 skip(N/A)；0=視為 fail
  #======================================
  # Cycle / wrapper 控制
  #======================================
  CYCLES: '1'# 循環次數（整數 >=1）
  CYCLE_INTERVAL: '60'# 每次循環間隔（秒）
  STOP_ON_FAIL: '0'         # 0=失敗繼續；1=失敗即停
  ORIGINAL_ENTRY: main_impl.py:run  # 真正主流程入口（module:function）


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
  PDU_RESET_SCRIPT: '/home/da40/charter/tools/pdu_outlet2.py'
  PDU_RESET_ACTION: reset
  PDU_RESET_WAIT_SEC: '120'
  PDU_RESET_TIMEOUT_SEC: '600'

  #======================================
  # Tools (control PC)
  #======================================
  TOOLS_PATH: /home/da40/charter/tools  # 工具目錄（control PC）
  TOOLS_PYTHON: python3                 # Python 執行檔（control PC）

  #======================================
  # WAN IPv6 取得方式 / 驗證條件
  #======================================
  WAN_IPV6_METHOD: ssh     # ssh|serial：取得 WAN IPv6 的主要方法
  WAN_IPV6_RETRIES: '12'   # 取得 WAN IPv6 重試次數（整數）
  WAN_IPV6_WAIT_MS: '700'  # 每次重試等待（毫秒）
  REQUIRE_PREFIXLEN_128: '0'  # '1' 強制要求 /128；'0' 不強制（依 test plan）

  #======================================
  # SSH 前置條件（re-arm / ssh-ready）+ cache
  #======================================
  ENABLE_SSH_PRECOND: '1'          # 1=啟用前置檢查（建議 customer 開）
  SSH_PRECOND_CACHE_ENABLED: '1'   # 1=使用快取，避免每步重複 re-arm
  SSH_PRECOND_CACHE_TTL_SEC: '600' # 快取有效時間（秒）

  #======================================
  # CPE 連線（SSH）
  #======================================
  CPE_IP: 192.168.1.1         # CPE 管理 IP（通常 LAN side）
  SSH_USER: operator           # SSH 使用者
  SSH_PASSWORD: <fill>

  #======================================
  # 客戶 / NOC profiles（customer 環境）
  #======================================
  CUSTOMER_ID: '682d4e5179b80027cd6fb27e'# 客戶/專案識別
  NOC_PROFILE: SPECTRUM_INT               # profiles.json 內的 profile 名稱
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
  # ^ 敏感：檔案請 chmod 600，且不要提交 repo

  #======================================
  # Console / Serial（必要時 fallback 或取介面資訊）
  #======================================
  # ^ 串口設備（依現場可能不同）
  CPE_BAUD: '115200'     # 串口 baud rate（常見 115200）
  CPE_USER: root         # console login 使用者
  CPE_PASSWORD: <fill>
  CPE_IFACE: br-wan      # CPE 上 WAN 介面名稱（用於抓 WAN IPv6 / metrics）

  #======================================
  # API / Timing（降低 race condition）
  #======================================
  API_BASE: http://127.0.0.1:8080  # 本機 sidecar/service base（若流程會呼叫）
  SERIAL_SETTLE_MS: '800'          # 串口登入後穩定等待（毫秒）
  STEP_WAIT_BEFORE_MS: '100'       # 每步驟前等待（毫秒）
  STEP_WAIT_AFTER_MS: '100'        # 每步驟後等待（毫秒）
  WAIT_AFTER_STEP1_MS: '200'       # step1 後額外等待（毫秒）
  WAIT_AFTER_STEP2_MS: '200'       # step2 後額外等待（毫秒）
  WAIT_AFTER_STEP3_MS: '1200'      # step3 後額外等待（毫秒）

  #======================================
  # Step2: ping6 目標與方法
  #======================================
  CPE_PING6_1: 2001:4860:4860::8888  # 目標1（Google DNS IPv6）
  CPE_PING6_2: 2606:4700:4700::1111  # 目標2（Cloudflare IPv6）
  PING_METHOD: 'ssh'                 # 'ssh'|'serial'|''(auto)
  # ^ 留空 ''：自動選擇（通常 WAN_IPV6_METHOD=ssh 會偏向 ssh）
  SSH_PING_TIMEOUT_SEC: '15'         # ssh ping 指令 timeout（秒）
  SSH_PING_COUNT: '1'                # ping 次數（建議 1~3）

  #======================================
  # Step3: metrics 方法（取得 WAN/route/addr 等）
  #======================================
  METRICS_METHOD: 'ssh'          # ssh|serial：metrics 取得方式
  SSH_METRICS_TIMEOUT_SEC: '25'  # metrics 指令 timeout（秒）

  #======================================
  # 通用重試 / 輸出控制
  #======================================
  RETRIES: '3'           # 通用重試次數（整數）
  INTERVAL_SEC: '1'      # 每次重試間隔（秒）
  SHOW_METRICS: '1'      # 1=顯示 metrics；0=不顯示
  ECHO_METRICS: '1'      # 1=把 metrics echo 到 log
  ECHO_MAX_LINES: '12'   # 最多輸出幾行，避免 log 過大
  DEBUG_METRICS: '0'     # 1=更多 debug log

  #======================================
  # 額外工具
  #======================================
  CPE_INFO_BIN: /home/da40/charter/tools/cpe_info  # 若流程會呼叫 cpe_info

  #======================================
  # Control PC 網路 / PDU / Profile
  #======================================
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
