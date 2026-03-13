# C15807947_Factory_Reset_DHCP_Reservation

- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_140=5188`
- 版本（manifest version）：`v2-noc-dhcp-reserved-factoryreset-verify-serialmute-1`
- Entrypoint：`cycle_wrapper.py:run`

> 本頁由工具依 11F_140 最新 export zip 自動產生/更新（2026-03-10）。

## 一句話說明

- DHCP reservation CRUD/穩定性驗證


## 你需要準備什麼（Preconditions）

- 平台服務正常：web/api/worker
- tools 可用：`/home/da40/charter/tools`
- secrets 不要寫死在 manifest（NOC/SSH/Warehouse 等一律用 `<fill>`/`.secrets`）


## 你只要改哪些參數（Top env）

- `TOOLS_PATH`: `/home/da40/charter/tools`
- `PROFILES_FILE`: `/home/da40/charter/.secrets/noc_profiles.json`
- `NOC_PROFILE`: `SPECTRUM_INT`
- `CUSTOMER_ID`: `682d4e5179b80027cd6fb27e`
- `CPE_HOST`: `192.168.1.1`
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
      CPE_HOST: 192.168.1.1
      SSH_PASSWORD: <fill>
    ```


??? note "manifest.yaml（流程參數完整；帳密/API key 已遮蔽）"

    ```yaml
    name: C15807947_Factory_Reset_DHCP_Reservation
    suite: sanity
    version: v2-noc-dhcp-reserved-factoryreset-verify-serialmute-1
    entrypoint: cycle_wrapper.py:run
    env:
      TEST_NAME: C15807947_Factory_Reset_DHCP_Reservation
      CYCLE_INTERVAL_SEC: '60'
      STOP_ON_FAIL: '1'
      TOOLS_PATH: /home/da40/charter/tools
      NOC_PROFILE: SPECTRUM_INT
      PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
      CUSTOMER_ID: 682d4e5179b80027cd6fb27e
      NOC_BASE: ''
      NOC_EMAIL: ''
      NOC_PASSWORD: ''
      CPE_HOST: 192.168.1.1
      CPE_SSH_PORT: '22'
      CPE_SSH_USER: operator
      SSH_PASSWORD: <fill>
      SSH_READY_CMD: uptime
      SSH_SCAN_TIMEOUT_SEC: '60'
      SSH_SCAN_INTERVAL_SEC: '2'
      SSH_ENABLE_RETRIES: '2'
      SSH_ENABLE_WAIT_SEC: '60'
      SSH_ENABLE_TIMEOUT_MIN: '120'
      CLOUD_READY_TIMEOUT_SEC: '30'
      CLOUD_READY_INTERVAL_SEC: '3'
      TEST_HOSTNAME: lan_test0
      LAN_TEST_MAC: 02:11:22:33:44:55
      TEST_RESERVED_IP: 192.168.1.222
      ON_IP_CONFLICT: pick_free
      RESERVED_IP_POOL_START: '200'
      RESERVED_IP_POOL_END: '250'
      DHCP_DUMP_RETRIES: '3'
      DHCP_DUMP_RETRY_WAIT_SEC: '2'
      RESERVED_WAIT_TIMEOUT_SEC: '180'
      RESERVED_WAIT_INTERVAL_SEC: '5'
      RESERVED_REQUIRE_HOSTNAME: '0'
      DO_FACTORY_RESET: '1'
      RESET_MUTE_SECS: '120'
      SERIAL_MUTE_STRICT: '0'
      FACTORY_RESET_MODE: full
      POST_RESET_CLOUD_TIMEOUT_SEC: '600'
      POST_RESET_CLOUD_INTERVAL_SEC: '5'
      POST_RESET_NO_RESV_TIMEOUT_SEC: '600'
      POST_RESET_NO_RESV_INTERVAL_SEC: '10'
      CYCLES: '1'
      CYCLE_INTERVAL: 70
      NODE_ID_MAX_RETRIES: 10
    ```
