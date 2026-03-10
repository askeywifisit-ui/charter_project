# C15807129_SSH_allowed_WAN_IP_from_LAN_Client_profile

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_131=51` / `11F_140=5096`
- 風險等級（對 DUT 影響）：**HIGH**

## 目的（Purpose）
SSH 權限/限制驗證（允許/拒絕/port/session/credential）。

## 前置條件（Preconditions）
- CPE/Cloud 需可連線（Internet/Cloud Connected）
- 需要的工具：`/home/da40/charter/tools`

## 測試行為摘要（What it does）
- SSH enable
- 依 case 嘗試登入/port/credential
- assert allow/deny 條件

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
name: C15807129_SSH_allowed_WAN_IP_from_LAN_Client_profile
version: v1
suite: sanity
entrypoint: cycle_wrapper.py:run
entry: cycle_wrapper.py:run
env:

  # =========================
  # [Wrapper / 測試循環控制]
  # - CYCLES：總共跑幾輪
  # - CYCLE_INTERVAL：每輪之間等待秒數
  # - STOP_ON_FAIL：遇到 fail 是否立刻停（1=立刻停 / 0=不中斷）
  # - ORIGINAL_ENTRY：wrapper 內部要呼叫的原始程式入口（通常不用改）
  # =========================

  CYCLES: '1'
  CYCLE_INTERVAL: '70'
  STOP_ON_FAIL: 1
  ORIGINAL_ENTRY: main_impl_orig.py:run

  # =========================
  # [工具路徑 / 基本資訊工具]
  # - TOOLS_PATH：tools 目錄
  # - METRICS_TOOL：收集 CPE 指標工具
  # - CPE_INFO_TOOL：讀取 CPE 狀態/版本/介面等資訊
  # - CPE_SSH_TOOL：SSH 控制工具（enable/disable/check...）
  # =========================

  TOOLS_PATH: /home/da40/charter/tools
  METRICS_TOOL: /home/da40/charter/tools/cpe_metrics_agent_serial.py
  CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
  CPE_SSH_TOOL: /home/da40/charter/tools/cpe_ssh.py

  # =========================
  # [Node ID 取得重試]
  # - NODE_ID_MAX_RETRIES：最多重試次數
  # - NODE_ID_RETRY_INTERVAL_SEC：每次重試間隔秒數
  # =========================

  NODE_ID_MAX_RETRIES: 10
  NODE_ID_RETRY_INTERVAL_SEC: 5

  # =========================
  # [CPE Console / Serial 連線]
  # - CPE_DEV/CPE_BAUD：serial 裝置與 baudrate
  # - CPE_USER/CPE_PASSWORD：登入用帳密（CPE_PASSWORD 可為 null 代表由程式自行處理）
  # =========================

  CPE_BAUD: 115200
  CPE_USER: root
  CPE_PASSWORD: null

  # =========================
  # [NOC / Cloud 設定]
  # - NOC_BASE：NOC API base URL
  # - NOC_EMAIL/NOC_PASSWORD：登入用帳密（建議放 secrets，不要寫死）
  # - CUSTOMER_ID：客戶帳號/設備對應的 customer id
  # - NOC_PROFILE + PROFILES_FILE：若程式支援，可用 profile 方式載入 base/email/password
  # - NOC_PROFILES_PATH：與 PROFILES_FILE 類似，若兩者同時存在通常屬於相容/重複參數
  # =========================

  NOC_BASE: https://piranha-int.tau.dev-charter.net
  NOC_EMAIL: <fill>
  NOC_PASSWORD: <fill>
  CUSTOMER_ID: '682d4e5179b80027cd6fb27e'
  NOC_PROFILE: SPECTRUM_INT
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
  NOC_PROFILES_PATH: /home/da40/charter/.secrets/noc_profiles.json

  # =========================
  # [SSH 測試參數（LAN → WAN）]
  # - SSH_USER/SSH_PASSWORD：CPE SSH 登入帳密
  # - SSH_TIMEOUT_MIN：整體流程 timeout（分鐘）
  # - SSH_HOST_LAN：從 LAN 端連線的 CPE 管理 IP
  # - SSH_TOOL_TIMEOUT：單次工具呼叫 timeout（秒）
  # - ENABLE_SSH_FLOW：是否啟用確保 SSH 可用的流程
  # - LAN_SSH_REQUIRED：是否要求 LAN SSH 必須可用
  # - WAN_SSH_TIMEOUT_SEC：嘗試 WAN SSH 的 timeout（秒）
  # =========================

  SSH_USER: operator
  SSH_PASSWORD: <fill>
  SSH_TIMEOUT_MIN: 120
  SSH_HOST_LAN: 192.168.1.1
  SSH_TOOL_TIMEOUT: 15
  ENABLE_SSH_FLOW: 1
  LAN_SSH_REQUIRED: 1
  WAN_SSH_TIMEOUT_SEC: 30

  # =========================
  # [測試模式 / IPv6]
  # - TEST_PROFILE：lab/customer 等情境（依程式定義）
  # - ENABLE_IPV6：auto/1/0（依程式定義；auto 代表自動偵測）
  # =========================

  ENABLE_IPV6: auto

  # =========================
  # [連線檢查 / PBR 介面指定]
  # - PING_IFACE：指定從哪個介面做 ping/route 相關檢查（依程式定義）
  # =========================


  # =========================
  # [電源控制（若測試需要）]
  # - PDU_SCRIPT：PDU 控制腳本路徑
  # - PDU_OUTLET_ID：PDU outlet 編號
  # =========================
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
