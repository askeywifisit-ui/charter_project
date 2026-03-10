# C15807130_SSH_allowed_local_IP_from_WLAN_Client

> 注意：此腳本名稱含 `5097__` 前綴，代表平台上目前的 script name 就是這樣（多半源自匯入 zip 檔名）。

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_131=52`
- 風險等級（對 DUT 影響）：**MEDIUM**

## 目的（Purpose）
驗證 WLAN client（Wi‑Fi）端能以 local IP SSH 進 CPE（需透過 NOC enable SSH）。

## manifest.yaml（節錄）
```yaml
# =========================
# [Manifest 基本資訊]
# - name/version/suite：系統辨識與分類用
# - entrypoint/entry：腳本入口（entry 多半為相容欄位）
# =========================

name: C15807130_SSH_allowed_local_IP_from_WLAN_Client
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
  WIFI_IWD_TOOL: /home/da40/charter/tools/wifi_iwd.py
  WIFI_NM_TOOL: /home/da40/charter/tools/wifi_nm.py

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
  ENABLE_IPV6: false

  # =========================
  # [測試環境 / 其他]
  # - PING_IFACE：control PC 端要使用的介面（例如 eno2）
  # - PDU_SCRIPT/PDU_OUTLET_ID：若需控制電源/插座，指定 PDU 工具與 outlet
  # =========================

  # ===============================
  # WLAN client (test platform Wi-Fi NIC)
  # Reference: C00000003_WIFI_basic_test
  # ===============================
  ENABLE_WIFI_CONNECT: "1"
  # WIFI_METHOD: auto|iwd|nm
  WIFI_METHOD: iwd
  # WIFI_BAND: 2g|5g|6g|"" (empty means any)
  WIFI_BAND: ""
  WIFI_TIMEOUT_SEC: "70"
  WIFI_DHCP_TIMEOUT_SEC: "60"
  WIFI_NM_RETRIES: "2"
  WIFI_DISCONNECT_ON_EXIT: "1"   # kept for compatibility; script also enforces disconnect via atexit

  # Wi-Fi credential source
  # - SSID/PSK will be queried from CPE via `cpe_ssh.py --cmd wifi-creds` (ref: C00000003)
  WIFI_CRED_PREFER: "current"
  # (Optional) If you want to override, set WIFI_SSID/WIFI_PSK.
  WIFI_SSID: ""
  WIFI_PSK: ""

  # Enforce that SSH validation is executed from WLAN source IP.
  WLAN_REQUIRED: "1"
  # Link-local IPv6 test control
  ENABLE_LL_IPV6_TEST: "1"
\g<1>\"0\"
\g<1>\"0\"
  WIFI_CARRIER_WAIT_SEC: "30"
  # CPE LAN interface for link-local IPv6 address
  LAN_LL_IPV6_IFACE: "br-home"
  LAN_LL_IPV6_CMD: "ifconfig br-home"
  # avoid hitting CPE single-SSH limitation back-to-back
  SSH_SERIALIZE_DELAY_SEC: "1"

LL_IPV6_REQUIRED: "1"

WIFI_LL_IPV6_REQUIRED: "1"
```
