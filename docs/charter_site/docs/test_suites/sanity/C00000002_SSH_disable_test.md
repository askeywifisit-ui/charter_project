# C00000002_SSH_disable_test

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_131=41` / `11F_140=5163`
- 風險等級（對 DUT 影響）：**HIGH**

## 目的（Purpose）
驗證 SSH disable 後不可再連線（安全性）。

## 前置條件（Preconditions）
- CPE/Cloud 需可連線（Internet/Cloud Connected）
- 需要的工具：`/home/da40/charter/tools`

## 測試行為摘要（What it does）
- 確保 SSH 已 enable（或可控）
- 執行 disable
- 確認 port 22/SSH 連線失敗

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
name: C00000002_SSH_disable_test
version: v1
suite: sanity
entrypoint: cycle_wrapper.py:run
env:
  # Wrapper controls
  CYCLES: '1'
  CYCLE_INTERVAL: '70'
  STOP_ON_FAIL: '1'
  ORIGINAL_ENTRY: main_impl.py:run

  # Tools / profiles
  TOOLS_PATH: /home/da40/charter/tools
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
  NOC_PROFILE: SPECTRUM_INT

  # NOC creds: leave empty here; filled by PROFILES_FILE or runner env injection
  NOC_BASE: ''
  CUSTOMER_ID: '682d4e5179b80027cd6fb27e'
  NOC_EMAIL: ''
  NOC_PASSWORD: ''
  LOCATION_ID: ''
  BEARER: '0'
  INSECURE: '0'

  # CPE
  CPE_HOST: '192.168.1.1'
  CPE_SSH_PORT: '22'
  CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
  CPE_INFO_TIMEOUT_SEC: '30'

  # CPE ready retry
  CPE_READY_MAX_RETRIES: '10'
  CPE_READY_RETRY_SLEEP_SEC: '30'

  # Disable + verify
  WAIT_AFTER_SSH_DISABLE_SEC: '60'
  SSH_DISABLE_VERIFY: '1'
  SSH_DISABLE_VERIFY_TIMEOUT_SEC: '120'
  SSH_DISABLE_VERIFY_INTERVAL_SEC: '2'

  # Logging
  LOG_INCLUDE_TS: '0'
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
