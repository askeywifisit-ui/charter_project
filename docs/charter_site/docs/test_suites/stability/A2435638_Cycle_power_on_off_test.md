# A2435638_Cycle_power_on_off_test

- Suite: **stability**
- Script ID（可能因 delete/import 變動）：`11F_140=5115`
- 版本（manifest version）：`v7-ssh-enable-profile-compat`
- Entrypoint：`cycle_wrapper.py:run`

> 本頁由工具依 11F_140 最新 export zip 自動產生/更新（2026-03-10）。

## 一句話說明

- （依腳本實作為準）


## 你需要準備什麼（Preconditions）

- 平台服務正常：web/api/worker
- tools 可用：`/home/da40/charter/tools`
- secrets 不要寫死在 manifest（NOC/SSH/Warehouse 等一律用 `<fill>`/`.secrets`）


## 你只要改哪些參數（Top env）

- `TOOLS_PATH`: `/home/da40/charter/tools`
- `PROFILES_FILE`: `/home/da40/charter/.secrets/noc_profiles.json`
- `NOC_PROFILE`: `SPECTRUM_INT`
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
      SSH_USER: operator
      SSH_PASSWORD: <fill>
    ```


??? note "manifest.yaml（流程參數完整；帳密/API key 已遮蔽）"

    ```yaml
    name: A2435638_Cycle_power_on_off_test
    suite: stability
    version: v7-ssh-enable-profile-compat
    entrypoint: cycle_wrapper.py:run
    env:
      CYCLES: '1'
      CYCLE_INTERVAL: '60'
      STOP_ON_FAIL: '0'
      ORIGINAL_ENTRY: main_impl.py:run
      CPE_BAUD: '115200'
      CPE_USER: root
      CPE_PASSWORD: ''
      CPE_IFACE: br-wan
      API_BASE: http://127.0.0.1:8080
      SERIAL_SETTLE_MS: '300'
      STEP_WAIT_BEFORE_MS: '0'
      STEP_WAIT_AFTER_MS: '100'
      WAIT_AFTER_POWER_OFF_MS: '1000'
      WAIT_AFTER_POWER_ON_MS: '3000'
      READY_RETRIES: '60'
      READY_INTERVAL_MS: '1000'
      POWER_OFF_CMD: ''
      POWER_ON_CMD: ''
      POWER_CMD_TIMEOUT_SEC: '20'
      CPE_PING1: 8.8.8.8
      RETRIES: '60'
      INTERVAL_SEC: '1'
      STRICT_PING: '0'
      SHOW_METRICS: '1'
      ECHO_METRICS: '1'
      ECHO_MAX_LINES: '12'
      DEBUG_METRICS: '0'
      POWER_OFF_SEC: '10'
      SETTLE_SEC: '120'
      CHECK_CMD: ''
      FINAL_STATUS_CHECK: '1'
      CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
      CPE_INFO_TIMEOUT_SEC: '90'
      TOOLS_PATH: /home/da40/charter/tools
      CPE_SSH_TOOL: /home/da40/charter/tools/cpe_ssh.py
      SSH_HOST_LAN: 192.168.1.1
      SSH_USER: operator
      SSH_PASSWORD: <fill>
      REQUIRE_SSH_READY: '1'
      AUTO_SSH_ENABLE: '1'
      NOC_PROFILE: SPECTRUM_INT
      PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
      SSH_TIMEOUT_MIN: '120'
      SSH_READY_WAIT_SEC: '90'
    ```
