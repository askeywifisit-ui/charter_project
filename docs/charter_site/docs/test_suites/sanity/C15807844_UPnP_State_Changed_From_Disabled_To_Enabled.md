# C15807844_UPnP_State_Changed_From_Disabled_To_Enabled



---

## 來源與下載

- GitHub scripts 目錄：<https://github.com/askeywifisit-ui/charter_project/tree/main/scripts/sanity>


### Export script zip（API）

> 說明：`script_id` 可能因 delete/import 變動；建議以 `suite+name` 查到 id 後再 export。

```bash
export CONTROL_PC_IP="172.14.1.140"
export CHARTER_BASE="http://${CONTROL_PC_IP}:5173"
export SUITE="sanity"
export NAME="C15807844_UPnP_State_Changed_From_Disabled_To_Enabled"

curl -fsSL "$CHARTER_BASE/api/scripts?limit=2000" -o /tmp/scripts.json

SCRIPT_ID=$(python3 - <<'PY'
import json,os
xs=json.load(open('/tmp/scripts.json'))
name=os.environ.get('NAME')
suite=os.environ.get('SUITE')
ms=[s for s in xs if s.get('suite')==suite and s.get('name')==name]
print(ms[0]['id'] if ms else "")
PY
)

echo "SCRIPT_ID=$SCRIPT_ID"
mkdir -p backup_scripts
curl -fsSL "$CHARTER_BASE/api/scripts/$SCRIPT_ID/export" \
  -o "backup_scripts/${NAME}_${SCRIPT_ID}.zip"
ls -lh "backup_scripts/${NAME}_${SCRIPT_ID}.zip"
```
- Suite: **sanity**
- Script ID（可能因 delete/import 變動）：`11F_140=5183`
- 版本（manifest version）：`v5`
- Entrypoint：`cycle_wrapper.py:run`

> 本頁由工具依 11F_140 最新 export zip 自動產生/更新（2026-03-10）。

## 一句話說明

- UPnP enable/disable 與狀態驗證


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
      CPE_HOST: 192.168.1.1
      SSH_USER: operator
      SSH_PASSWORD: <fill>
    ```


??? note "manifest.yaml（流程參數完整；帳密/API key 已遮蔽）"

    ```yaml
    name: C15807844_UPnP_State_Changed_From_Disabled_To_Enabled
    suite: sanity
    version: v5
    entrypoint: cycle_wrapper.py:run
    env:
      CYCLES: '1'
      CYCLE_INTERVAL: '70'
      STOP_ON_FAIL: 1
      ORIGINAL_ENTRY: main_impl_orig.py:run_verify_upnp
      TOOLS_PATH: /home/da40/charter/tools
      METRICS_TOOL: /home/da40/charter/tools/cpe_metrics_agent_serial.py
      NODE_ID_MAX_RETRIES: 10
      NODE_ID_RETRY_INTERVAL_SEC: 2
      CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
      CPE_SSH_TOOL: /home/da40/charter/tools/cpe_ssh.py
      CPE_BAUD: 115200
      CPE_USER: root
      CPE_PASSWORD: null
      NOC_BASE: https://piranha-int.tau.dev-charter.net
      NOC_EMAIL: <fill>
      NOC_PASSWORD: <fill>
      CUSTOMER_ID: 682d4e5179b80027cd6fb27e
      NOC_PROFILE: SPECTRUM_INT
      PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
      SSH_USER: operator
      SSH_PASSWORD: <fill>
      SSH_TIMEOUT_MIN: 120
      SSH_REENABLE_EACH_CYCLE: 0
      SSH_HOST_LAN: 192.168.1.1
      WAN_SSH_REQUIRED: 1
      LAN_SSH_REQUIRED: 1
      SSH_TOOL_TIMEOUT: 15
      USE_CLOUD_SSH: '1'
      CPE_LOG_TIMEOUT_SEC: '240'
      SSH_ACTION: enable
      ENABLE_NOC_API_TESTS: 1
      SPEEDTEST_WAIT_SEC: 60
      ENABLE_SPEEDTEST: 1
      ENABLE_WIFI_TEST: 0
      ENABLE_LTE_TEST: 0
      ENABLE_SSH_FLOW: 1
      SSH_RECOVER_ON_FAIL: 1
      SSH_RECOVER_WAIT_SEC: 2
      SSH_RECOVER_GRACE_SEC: 5
      UPNP_HEALTH_TIMEOUT_SEC: 180
      SPEEDTEST_MAX_TRIES: 3
      SPEEDTEST_INTERVAL_SEC: 10
      CPE_HEALTH_WAIT_SEC: '40'
      ENABLE_DNS_CHECK: 0
      TARGET: www.google.com
      SECOND: cloudflare.com
      EXPECT_A_MIN: 1
      EXPECT_AAAA_MIN: 1
      RETRIES: 3
      INTERVAL_SEC: 3
      DNS_SSH_TIMEOUT_SEC: 30
      UPNP_ITERATIONS: 1
      UPNP_LOG_GREP: upnp
      UPNP_LOG_LINES: 100
      UPNP_LOG_WINDOW_MIN: 5
      CPE_HOST: 192.168.1.1
      UPNP_APPLY_WAIT_SEC: 10
      UPNP_REBOOT_WAIT_SEC: 60
      INTERNET_STATUS_MAX_RETRIES: 20
      INTERNET_STATUS_INTERVAL_SEC: 3
      REBOOT_MUTE_SECS: 60
      REBOOT_MUTE_WITH_LOCK: 1
      ENABLE_UPNP_HEALTH: 1
      UPNP_RESTORE_BASELINE: 0
      SSH_PORT_MAX_RETRIES: 20
      SSH_PORT_INTERVAL_SEC: 3
      UPNP_POST_REBOOT_SSH_REARM: 1
      UPNP_POST_REBOOT_SSH_PORT_TIMEOUT_SEC: 300
      UPNP_POST_REBOOT_SSH_RETRY_ON_FAIL: 1
    ```
