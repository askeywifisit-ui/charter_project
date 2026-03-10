# C24541455_Multiple_speedtest

- Suite: **stability**
- Script ID（可能因 delete/import 變動）：`11F_140=5120`
- 版本（manifest version）：`v4-professional-customerid-manifest-cycle_tags`
- Entrypoint：`cycle_wrapper.py:run`

> 本頁由工具依 11F_140 最新 export zip 自動產生/更新（2026-03-10）。

## 一句話說明

- 速度測試/長跑穩定性驗證


## 你需要準備什麼（Preconditions）

- 平台服務正常：web/api/worker
- tools 可用：`/home/da40/charter/tools`
- secrets 不要寫死在 manifest（NOC/SSH/Warehouse 等一律用 `<fill>`/`.secrets`）


## 你只要改哪些參數（Top env）

- `TOOLS_PATH`: `/home/da40/charter/tools`
- `PROFILES_FILE`: `/home/da40/charter/.secrets/noc_profiles.json`
- `NOC_PROFILE`: `SPECTRUM_INT`
- `CUSTOMER_ID`: `682d4e5179b80027cd6fb27e`
- `SSH_USER`: `operator`
- `SSH_PASSWORD`: `<fill>`


## Run（API）

```bash
export CHARTER_BASE="http://<CONTROL_PC_IP>:5173"
SCRIPT_ID=<SCRIPT_ID_11F_140>
# 建議先確認 worker 正常
curl -fsSL "$CHARTER_BASE/api/runs/worker/status" | python3 -m json.tool
# 送出 run
curl -sS -X POST "$CHARTER_BASE/api/scripts/$SCRIPT_ID/run" | python3 -m json.tool
```


## 怎麼看結果（Evidence）

```bash
RID=<RUN_ID>
curl -sS "$CHARTER_BASE/api/runs/$RID/log" > run_${RID}_log.json
# 若 fail-hook 有產生 cpe logs
curl -sS "$CHARTER_BASE/api/runs/$RID/log-archives" | python3 -m json.tool
curl -fsSL "$CHARTER_BASE/api/runs/$RID/log-archive" -o run_${RID}_cpe_log.tar.gz
```


## Cleanup

```bash
# 清理已完成的 runs + workdir（避免磁碟累積）
curl -sS -X DELETE "$CHARTER_BASE/api/runs/purge?older_than_days=0" | python3 -m json.tool
```


??? note "manifest.yaml（節錄：常用 env）"

    ```yaml
    env:
      TOOLS_PATH: /home/da40/charter/tools
      PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
      NOC_PROFILE: SPECTRUM_INT
      CUSTOMER_ID: 682d4e5179b80027cd6fb27e
      SSH_USER: operator
      SSH_PASSWORD: <fill>
    ```


??? note "manifest.yaml（完整 env，已自動去敏）"

    ```yaml
    name: C24541455_Multiple_speedtest
    suite: stability
    version: v4-professional-customerid-manifest-cycle_tags
    entrypoint: cycle_wrapper.py:run
    env:
      CYCLES: '1'
      CYCLE_INTERVAL: 30
      STOP_ON_FAIL: 1
      PRECONDITION_FIRST_CYCLE: 1
      ORIGINAL_ENTRY: main_impl.py:run
      TOOLS_PATH: /home/da40/charter/tools
      CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
      CPE_SSH_TOOL: /home/da40/charter/tools/cpe_ssh.py
      NODE_ID_MAX_RETRIES: 30
      NOC_BASE: https://piranha-int.tau.dev-charter.net
      CUSTOMER_ID: 682d4e5179b80027cd6fb27e
      SSH_USER: operator
      SSH_PASSWORD: <fill>
      SSH_TIMEOUT_MIN: 120
      SSH_REENABLE_EACH_CYCLE: 0
      SSH_HOST_LAN: 192.168.1.1
      WAN_SSH_REQUIRED: 0
      LAN_SSH_REQUIRED: 1
      SSH_GATE_EACH_CYCLE: 1
      SSH_TOOL_TIMEOUT: 15
      USE_CLOUD_SSH: '1'
      CPE_LOG_TIMEOUT_SEC: '240'
      NOC_PROFILE: SPECTRUM_INT
      PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
      SSH_ACTION: enable
      ENABLE_NOC_API_TESTS: 1
      SPEEDTEST_WAIT_SEC: 60
      ENABLE_SPEEDTEST: 1
      ENABLE_WIFI_TEST: 0
      ENABLE_LTE_TEST: 0
      ENABLE_SSH_FLOW: 1
      SPEEDTEST_MAX_TRIES: 3
      SPEEDTEST_INTERVAL_SEC: 10
      INTERNET_CHECK_MAX_RETRIES: '10'
      INTERNET_CHECK_INTERVAL_SEC: '3'
      CPE_HEALTH_WAIT_SEC: '30'
      HEALTH_RECOVERY_RETRY: 1
      HEALTH_RECOVERY_ENABLE_SSH: 1
      HEALTH_RECOVERY_WAIT_AFTER_ENABLE_SEC: 60
      HEALTH_RECOVERY_PDU_RESET: 0
      HEALTH_RECOVERY_PDU_WAIT_SEC: 120
      ENABLE_DNS_CHECK: 0
      TARGET: www.google.com
      SECOND: cloudflare.com
      EXPECT_A_MIN: 1
      EXPECT_AAAA_MIN: 1
      RETRIES: 3
      INTERVAL_SEC: 3
      DNS_SSH_TIMEOUT_SEC: 30
    ```
