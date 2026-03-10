# C15807133_SSH_authorized_only_on_port_22

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_131=54` / `11F_140=5099`
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
name: C15807133_SSH_authorized_only_on_port_22
version: v1
suite: sanity
entrypoint: cycle_wrapper.py:run
entry: cycle_wrapper.py:run
env:

  # =========================
  # [Wrapper / 測試流程控制]
  # - CYCLES：總共跑幾輪
  # - CYCLE_INTERVAL：每輪間隔（秒）
  # - STOP_ON_FAIL：遇到 fail 是否立刻停止（1=停 / 0=不中斷）
  # - ORIGINAL_ENTRY：wrapper 內部實際呼叫的原始腳本入口（通常不用改）
  # =========================

  CYCLES: '1'
  CYCLE_INTERVAL: '70'
  STOP_ON_FAIL: 1
  ORIGINAL_ENTRY: main_impl_orig.py:run

  # =========================
  # [工具路徑 / 共用工具]
  # - TOOLS_PATH：tools 目錄
  # - METRICS_TOOL：收集 CPE metrics 的工具
  # - CPE_INFO_TOOL：查 CPE 基本資訊/狀態
  # - CPE_SSH_TOOL：執行 SSH enable/check 的工具
  # =========================

  TOOLS_PATH: /home/da40/charter/tools
  METRICS_TOOL: /home/da40/charter/tools/cpe_metrics_agent_serial.py
  CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
  CPE_SSH_TOOL: /home/da40/charter/tools/cpe_ssh.py

  # =========================
  # [Node ID / 裝置識別重試]
  # - NODE_ID_MAX_RETRIES：找不到 node_id 時最多重試次數
  # - NODE_ID_RETRY_INTERVAL_SEC：每次重試間隔（秒）
  # =========================

  NODE_ID_MAX_RETRIES: 10
  NODE_ID_RETRY_INTERVAL_SEC: 5

  # =========================
  # [Serial / Console 登入參數]
  # - CPE_DEV/CPE_BAUD：Console 裝置與 baudrate（依環境調整）
  # - CPE_USER/CPE_PASSWORD：登入用帳密（可為空/NULL，腳本可能會 fallback）
  # =========================

  CPE_BAUD: 115200
  CPE_USER: root
  CPE_PASSWORD: null

  # =========================
  # [NOC / Cloud Profile 與帳密來源]
  # - CUSTOMER_ID：雲端系統要操作的 customer/account id
  # - NOC_PROFILE：profiles.json 內的 profile 名稱（例如 SPECTRUM_INT）
  # - PROFILES_FILE/NOC_PROFILES_PATH：profiles JSON 路徑（內含 base/email/password）
  # - NOC_BASE/NOC_EMAIL/NOC_PASSWORD：若直接在 manifest 指定，通常會優先於 profile
  # =========================

  NOC_BASE: https://piranha-int.tau.dev-charter.net
  NOC_EMAIL: <fill>
  NOC_PASSWORD: <fill>
  CUSTOMER_ID: '682d4e5179b80027cd6fb27e'
  NOC_PROFILE: SPECTRUM_INT
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
  NOC_PROFILES_PATH: /home/da40/charter/.secrets/noc_profiles.json

  # =========================
  # [SSH Flow / 檢查項目]
  # - SSH_USER/SSH_PASSWORD：SSH 登入帳密
  # - SSH_HOST_LAN：CPE LAN 管理 IP
  # - SSH_TIMEOUT_MIN：整體 SSH 流程上限（分鐘）
  # - SSH_TOOL_TIMEOUT：單次工具呼叫 timeout（秒）
  # - ENABLE_SSH_FLOW：是否啟用 SSH 流程（1=啟用 / 0=停用）
  # - LAN_SSH_REQUIRED：LAN SSH 是否必須成功（1=必須 / 0=可略過）
  # =========================

  SSH_USER: operator
  SSH_PASSWORD: <fill>
  SSH_TIMEOUT_MIN: 120
  SSH_HOST_LAN: 192.168.1.1
  SSH_TOOL_TIMEOUT: 15
  ENABLE_SSH_FLOW: 1
  LAN_SSH_REQUIRED: 1

  # =========================
  # [本機連線檢查 / PBR 介面]
  # - PING_IFACE：本機要用來發 ping/檢查的介面（例：eno2）
  # =========================


  # =========================
  # [PDU / 供電控制（若測試需要）]
  # - PDU_SCRIPT：PDU 控制腳本路徑
  # - PDU_OUTLET_ID：要操作的 outlet 編號
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
