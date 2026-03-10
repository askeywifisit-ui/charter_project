# C15807134_SSH_only_1_session_per_username

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_131=55` / `11F_140=5100`
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
name: C15807134_SSH_only_1_session_per_username
version: v1
suite: sanity
entrypoint: cycle_wrapper.py:run
entry: cycle_wrapper.py:run
env:

  # =========================
  # [Wrapper / 測試流程控制]
  # - CYCLES：總共要跑幾輪
  # - CYCLE_INTERVAL：每輪之間等待秒數
  # - STOP_ON_FAIL：遇到 fail 是否立刻停止（1=停 / 0=不中斷）
  # - ORIGINAL_ENTRY：wrapper 內部要呼叫的原始腳本入口（通常不改）
  # =========================

  CYCLES: '1'
  CYCLE_INTERVAL: '70'
  STOP_ON_FAIL: 1
  ORIGINAL_ENTRY: main_impl_orig.py:run

  # =========================
  # [工具路徑 / 依賴工具]
  # - TOOLS_PATH：工具目錄（cpe_ssh/cpe_info/metrics 等）
  # - METRICS_TOOL：收集 CPE 指標工具
  # - CPE_INFO_TOOL：查詢 CPE 狀態/版本工具
  # - CPE_SSH_TOOL：執行 SSH 動作的工具腳本
  # =========================

  TOOLS_PATH: /home/da40/charter/tools
  METRICS_TOOL: /home/da40/charter/tools/cpe_metrics_agent_serial.py
  CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
  CPE_SSH_TOOL: /home/da40/charter/tools/cpe_ssh.py

  # =========================
  # [Node ID 取得重試]
  # - NODE_ID_MAX_RETRIES：取得 node_id 的最大重試次數
  # - NODE_ID_RETRY_INTERVAL_SEC：每次重試間隔秒數
  # =========================

  NODE_ID_MAX_RETRIES: 10
  NODE_ID_RETRY_INTERVAL_SEC: 5

  # =========================
  # [Console / Serial 登入參數]
  # - CPE_DEV：Serial 裝置路徑（依環境調整）
  # - CPE_BAUD：Serial baudrate（依環境調整）
  # - CPE_USER/CPE_PASSWORD：登入帳密（若留空/NULL，腳本可能走 fallback）
  # =========================

  CPE_BAUD: 115200
  CPE_USER: root
  CPE_PASSWORD: null

  # =========================
  # [NOC / Cloud Profile 與帳密]
  # - NOC_BASE：NOC API base URL
  # - NOC_EMAIL/NOC_PASSWORD：NOC 登入帳密（建議放 secrets）
  # - CUSTOMER_ID：要測的客戶/帳號 id
  # - NOC_PROFILE：profiles.json 內的 profile 名稱
  # - PROFILES_FILE/NOC_PROFILES_PATH：profiles 檔案路徑（通常放 .secrets）
  # =========================

  NOC_BASE: https://piranha-int.tau.dev-charter.net
  NOC_EMAIL: <fill>
  NOC_PASSWORD: <fill>
  CUSTOMER_ID: '682d4e5179b80027cd6fb27e'
  NOC_PROFILE: SPECTRUM_INT
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
  NOC_PROFILES_PATH: /home/da40/charter/.secrets/noc_profiles.json

  # =========================
  # [SSH 測試參數]
  # - SSH_HOST_LAN：CPE LAN 管理 IP（常見 192.168.1.1）
  # - SSH_USER/SSH_PASSWORD：SSH 登入帳密
  # - SSH_TIMEOUT_MIN：整體流程 timeout（分鐘）
  # - SSH_TOOL_TIMEOUT：單次工具呼叫 timeout（秒）
  # - ENABLE_SSH_FLOW：是否啟用 SSH enable/check 流程（1=啟用）
  # - LAN_SSH_REQUIRED：是否要求 LAN SSH 必須成功（1=必須）
  # - SSH_HOLD_SEC：第一個 session hold 秒數（用來驗證僅允許單一 session）
  # - SSH_SECOND_TIMEOUT_SEC：第二個 session 嘗試 timeout（秒）
  # =========================

  SSH_USER: operator
  SSH_PASSWORD: '<fill>'
  SSH_TIMEOUT_MIN: 120
  SSH_HOST_LAN: 192.168.1.1
  SSH_TOOL_TIMEOUT: 15
  ENABLE_SSH_FLOW: 1
  LAN_SSH_REQUIRED: 1
  SSH_HOLD_SEC: 60
  SSH_SECOND_TIMEOUT_SEC: 12

  # =========================
  # [其他連線 / PDU / 介面]
  # - PING_IFACE：Control PC 上要走的介面（例如 eno2）
  # - PDU_SCRIPT：控制電源的 PDU 腳本路徑
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
