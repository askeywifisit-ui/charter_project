# C15807131_SSH_not_allowed_wrong_credential

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_131=53` / `11F_140=5175`
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
name: C15807131_SSH_not_allowed_wrong_credential
version: v1
suite: sanity
entrypoint: cycle_wrapper.py:run
entry: cycle_wrapper.py:run
env:

  # =========================
  # [Wrapper / 循環流程控制]
  # - CYCLES: 循環次數（跑幾輪）
  # - CYCLE_INTERVAL: 每輪之間等待秒數
  # - STOP_ON_FAIL: 遇到失敗是否立刻停止（1=停 / 0=繼續）
  # - ORIGINAL_ENTRY: wrapper 內呼叫的原始腳本入口
  # =========================

  CYCLES: '1'
  CYCLE_INTERVAL: '70'
  STOP_ON_FAIL: 1
  ORIGINAL_ENTRY: main_impl_orig.py:run

  # =========================
  # [工具路徑 / 系統工具]
  # - TOOLS_PATH: 工具目錄（cpe_ssh / cpe_info 等）
  # - METRICS_TOOL: 收集/輸出 metrics 的工具
  # - CPE_INFO_TOOL: 取得 CPE 資訊/狀態工具
  # - CPE_SSH_TOOL: CPE SSH 工具路徑
  # =========================

  TOOLS_PATH: /home/da40/charter/tools
  METRICS_TOOL: /home/da40/charter/tools/cpe_metrics_agent_serial.py
  CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
  CPE_SSH_TOOL: /home/da40/charter/tools/cpe_ssh.py

  # =========================
  # [其他參數]
  # - NODE_ID_MAX_RETRIES: 等待/取得 node id 的最大重試次數
  # - CPE_DEV: 參數
  # - CPE_BAUD: 參數
  # - CPE_USER: 參數
  # - CPE_PASSWORD: 參數
  # =========================

  NODE_ID_MAX_RETRIES: 10

  # =========================
  # [重試 / Timeout / Interval]
  # - NODE_ID_RETRY_INTERVAL_SEC: node id 重試間隔（秒）
  # =========================

  NODE_ID_RETRY_INTERVAL_SEC: 5
  CPE_BAUD: 115200
  CPE_USER: root
  CPE_PASSWORD: null

  # =========================
  # [NOC / Profiles（雲端參數）]
  # - NOC_BASE: 參數
  # - NOC_EMAIL: 參數
  # - NOC_PASSWORD: 參數
  # - CUSTOMER_ID: NOC/雲端使用的 customer id
  # - NOC_PROFILE: profiles.json 內的 profile 名稱
  # - PROFILES_FILE: profiles.json 路徑
  # - NOC_PROFILES_PATH: （相容用）profiles.json 路徑
  # =========================

  NOC_BASE: https://piranha-int.tau.dev-charter.net
  NOC_EMAIL: <fill>
  NOC_PASSWORD: <fill>
  CUSTOMER_ID: '682d4e5179b80027cd6fb27e'
  NOC_PROFILE: SPECTRUM_INT
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
  NOC_PROFILES_PATH: /home/da40/charter/.secrets/noc_profiles.json

  # =========================
  # [SSH / 存取控制]
  # - SSH_USER: SSH 使用者
  # - SSH_PASSWORD: SSH 密碼
  # - SSH_TIMEOUT_MIN: SSH 流程總 timeout（分鐘）
  # - SSH_HOST_LAN: CPE LAN 管理 IP
  # - SSH_TOOL_TIMEOUT: 單次 SSH 工具 timeout（秒）
  # - ENABLE_SSH_FLOW: 是否啟用 SSH enable/check 流程
  # - LAN_SSH_REQUIRED: 是否要求 LAN SSH 必須可用（1=必須）
  # =========================

  SSH_USER: operator
  SSH_PASSWORD: <fill>
  SSH_TIMEOUT_MIN: 120
  SSH_HOST_LAN: 192.168.1.1
  SSH_TOOL_TIMEOUT: 15
  ENABLE_SSH_FLOW: 1
  LAN_SSH_REQUIRED: 1

  # =========================
  # [網路路徑 / 介面]
  # - PING_IFACE: Control PC 端要走的介面（例如 eno2）
  # =========================


  # =========================
  # [Power / PDU 斷電控制]
  # - PDU_SCRIPT: PDU 控制腳本路徑
  # - PDU_OUTLET_ID: PDU outlet id
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
