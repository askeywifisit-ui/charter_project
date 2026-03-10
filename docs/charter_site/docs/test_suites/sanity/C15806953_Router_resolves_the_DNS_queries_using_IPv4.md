# C15806953_Router_resolves_the_DNS_queries_using_IPv4

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_131=46` / `11F_140=5091`
- 風險等級（對 DUT 影響）：**HIGH**

## 目的（Purpose）
驗證 DNS 查詢解析（IPv4）。

## 前置條件（Preconditions）
- CPE/Cloud 需可連線（Internet/Cloud Connected）
- 需要的工具：`/home/da40/charter/tools`

## 測試行為摘要（What it does）
- 執行 DNS query（工具/命令）
- 比對解析結果/可達性

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
name: C15806953_Router_resolves_the_DNS_queries_using_IPv4
version: v2-DNS_queries_IPv4
suite: sanity
entrypoint: cycle_wrapper.py:run
entry: cycle_wrapper.py:run
env:
  # --- Cycle control (continuous DNSv4 Resolve) ----------
  # --- cycle_wrapper 設定 ---
  CYCLES: '1'
  CYCLE_INTERVAL: 70
  STOP_ON_FAIL: 1

  # cycle_wrapper 會依這個 entry 去找 module:func
  ORIGINAL_ENTRY: main_impl_orig.py:run

  # --- tools 相關 ---
  TOOLS_PATH: /home/da40/charter/tools
  METRICS_TOOL: /home/da40/charter/tools/cpe_metrics_agent_serial.py

  # --- CPE / serial ---
  CPE_BAUD: '115200'
  CPE_USER: root
  CPE_PASSWORD: ''
  CPE_IFACE: br-wan

  # --- NOC / API ---
  NOC_BASE: https://piranha-int.tau.dev-charter.net
  NOC_EMAIL: <fill>
  NOC_PASSWORD: <fill>
  CUSTOMER_ID: 682d4e5179b80027cd6fb27e
  BEARER: 0
  INSECURE: 0

  API_BASE: http://127.0.0.1:8080
  DISABLE_INTERNAL_LOGPULL: '1'
  USE_CLOUD_SSH: '1'
  CPE_LOG_TIMEOUT_SEC: '240'
  NOC_PROFILE: 'SPECTRUM_INT'
  PROFILES_FILE: '/home/da40/charter/.secrets/noc_profiles.json'

  # --- SSH 動作（透過 NOC 開啟 SSH）---
  ENABLE_SSH_FLOW: 1

  # NOC 啟用 SSH 的重試次數（避免偶發 NOC timeout）
  SSH_ENABLE_RETRIES: 3

  # --- ssh_ready 掃描 ssh port 的總等待秒數（預設 30）---
  SSH_SCAN_TIMEOUT_SEC: 30
  SSH_USER: 'operator'
  SSH_PASSWORD: <fill>
  SSH_TIMEOUT_MIN: '120'

  # --- health 前的 SSH port 檢查 ---
  CPE_HEALTH_HOST: '192.168.1.1'
  CPE_HEALTH_PORT: '22'
  SSH_PORT_CHECK_TIMEOUT: '3'

  # --- NOC API feature toggles ---
  # speedtest 開關（1=啟用, 0=關閉）
  ENABLE_SPEEDTEST: 0
  # WiFi 測試開關（1=啟用, 0=關閉）
  ENABLE_WIFI_TEST: 0
  # LTE 測試開關（1=啟用, 0=關閉）
  ENABLE_LTE_TEST: 0
  # health check 開關（1=啟用, 0=略過）
  ENABLE_HEALTH_CHECK: 0

  # --- DNS 檢查設定（重點）---
  # DNS 測試開關（1=啟用, 0=關閉）
  ENABLE_DNS_CHECK: 1

  TARGET: www.google.com
  # 第一個要查的 domain
  SECOND: www.o2.de
  # 第二個，可留空 '' 就不測

  # A record 至少要幾筆才算 PASS
  EXPECT_A_MIN: 1
  # AAAA 至少要幾筆；要關 IPv6 就改 0
  EXPECT_AAAA_MIN: 1

  RETRIES: 3
  INTERVAL_SEC: 3
  DNS_SSH_TIMEOUT_SEC: 30
  DNS_INVALID_IPS: 172.14.1.1, 127.0.0.53,223.255.255.1, 223.255.255.1    
  # 視為「不合法」的 DNS 回應 IP（逗號分隔，可自行擴充，依 site 調整）

  # --- debug 開關 ---
  # DEBUG_DNS=1 會輸出 IP 列表；平台 stdout 可能被截斷，建議預設關閉
  DEBUG_DNS: '0'
  DEBUG_SHOW_CMD: '0'

  # 將 DNS 結果寫入 run dir 的 JSON 檔，避免只看 stdout 被截斷
  SAVE_DNS_RESULTS: '1'
  DNS_RESULTS_FILE: dns_results.json
  # --- node_id retry (cpe_info --node-id) ---
  NODE_ID_MAX_TRIES: 3
  NODE_ID_INTERVAL_SEC: 2
  NODE_ID_CMD_TIMEOUT_SEC: 15
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
