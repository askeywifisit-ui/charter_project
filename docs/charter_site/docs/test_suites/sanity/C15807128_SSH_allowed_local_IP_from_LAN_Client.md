# C15807128_SSH_allowed_local_IP_from_LAN_Client

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_131=50` / `11F_140=5214`
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
name: C15807128_SSH_allowed_local_IP_from_LAN_Client
version: v2
suite: sanity
entrypoint: cycle_wrapper.py:run
entry: cycle_wrapper.py:run
env:
  # =========================
  # [Wrapper / 流程控制]
  # - CYCLES：執行輪數
  # - CYCLE_INTERVAL：每輪之間等待秒數
  # - STOP_ON_FAIL：失敗是否立刻停止（1=停 / 0=繼續跑）
  # - ORIGINAL_ENTRY：wrapper 內部呼叫的原始入口（通常不需改）
  # =========================
  CYCLES: '1'
  CYCLE_INTERVAL: '70'
  STOP_ON_FAIL: 1
  ORIGINAL_ENTRY: main_impl_orig.py:run

  # =========================
  # [工具路徑 / 基本工具]
  # - TOOLS_PATH：工具目錄
  # - METRICS_TOOL：收集 metrics 的工具
  # - CPE_INFO_TOOL：取得 CPE 狀態/版本資訊
  # - CPE_SSH_TOOL：CPE SSH 控制工具
  # =========================
  TOOLS_PATH: /home/da40/charter/tools
  METRICS_TOOL: /home/da40/charter/tools/cpe_metrics_agent_serial.py
  CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
  CPE_SSH_TOOL: /home/da40/charter/tools/cpe_ssh.py

  # =========================
  # [重試與等待]
  # - NODE_ID_MAX_RETRIES：取得 node_id 的最大重試次數
  # - NODE_ID_RETRY_INTERVAL_SEC：每次重試間隔（秒）
  # =========================
  NODE_ID_MAX_RETRIES: 10
  NODE_ID_RETRY_INTERVAL_SEC: 5

  # =========================
  # [Console / Serial 連線]
  # - CPE_DEV/CPE_BAUD：serial 裝置與 baudrate（依環境調整）
  # - CPE_USER/CPE_PASSWORD：登入帳密（密碼可為 null 由腳本 fallback）
  # =========================
  CPE_BAUD: 115200
  CPE_USER: root
  CPE_PASSWORD: null

  # =========================
  # [NOC / Profile / 認證]
  # - CUSTOMER_ID：要測的客戶/帳號 ID
  # - NOC_PROFILE/PROFILES_FILE：profiles 設定檔（建議用來避免寫死帳密）
  # - NOC_BASE/NOC_EMAIL/NOC_PASSWORD：若腳本採用直填模式則需提供
  # =========================
  NOC_BASE: https://piranha-int.tau.dev-charter.net
  NOC_EMAIL: <fill>
  NOC_PASSWORD: <fill>
  CUSTOMER_ID: '682d4e5179b80027cd6fb27e'
  NOC_PROFILE: SPECTRUM_INT
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
  NOC_PROFILES_PATH: /home/da40/charter/.secrets/noc_profiles.json

  # =========================
  # [SSH 參數]
  # - SSH_HOST_LAN：CPE LAN 管理 IP
  # - SSH_USER/SSH_PASSWORD：SSH 登入帳密
  # - SSH_TOOL_TIMEOUT：單次 ssh 工具呼叫 timeout（秒）
  # - ENABLE_SSH_FLOW：是否啟用「確保 SSH 可用」流程
  # - LAN_SSH_REQUIRED：是否要求 LAN SSH 必須成功
  # - TEST_PROFILE：測試情境（lab/customer）
  # - ENABLE_IPV6：是否執行 IPv6 步驟（auto/true/false）
  # - SSH_ENABLE_SETTLE_SEC：啟用 SSH 後的等待秒數（避免服務尚未就緒）
  # - SSH_CONNECT_RETRIES：SSH 驗證重試次數（遇到短暫拒絕/不穩定時）
  # - SSH_CONNECT_RETRY_WAIT_SEC：重試間隔秒數
  # - SSH_FORCE_SHELL：強制使用互動 shell 模式驗證（避開 exec request failed）0/1
  # =========================
  SSH_USER: operator
  SSH_PASSWORD: <fill>
  SSH_TIMEOUT_MIN: 120
  SSH_HOST_LAN: 192.168.1.1
  SSH_TOOL_TIMEOUT: 15
  SSH_ENABLE_SETTLE_SEC: 2
  SSH_CONNECT_RETRIES: 3
  SSH_CONNECT_RETRY_WAIT_SEC: 2
  SSH_FORCE_SHELL: 0
  ENABLE_SSH_FLOW: 1
  LAN_SSH_REQUIRED: 1

  # =========================
  # [IPv6 行為控制]
  # 說明：此用例除了 LAN IPv4 外，也會驗證「LAN Global IPv6(應允許)」與
  #       「LAN Link-local IPv6(應拒絕)」。
  #
  # 為了讓「lab(可能沒有 IPv6)」與「customer(通常有 IPv6)」共用同一支腳本，
  # 提供以下兩個參數：
  #
  # 1) TEST_PROFILE
  #    - customer：預設會嘗試執行 IPv6 步驟（受 ENABLE_IPV6 影響）
  #    - lab     ：預設跳過 IPv6 步驟（避免 lab 無 IPv6 時誤判 fail）
  #
  # 2) ENABLE_IPV6
  #    - auto ：（預設）若偵測不到 IPv6（無 global/LL）則自動 skip IPv6 步驟
  #    - true ：強制執行 IPv6 檢查；若無法取得需要的 IPv6 位址則 FAIL
  #    - false：強制跳過 IPv6 步驟
  # =========================
  ENABLE_IPV6: auto

  # =========================
  # [測試環境 / 其他]
  # - PING_IFACE：control PC 端要使用的介面（例如 eno2）
  # - PDU_SCRIPT/PDU_OUTLET_ID：若需控制電源/插座，指定 PDU 工具與 outlet
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
