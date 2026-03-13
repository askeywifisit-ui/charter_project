# C15806945_WiFi_radio_enable_disable_longrun



---

## 來源與下載

- GitHub scripts 目錄：<https://github.com/askeywifisit-ui/charter_project/tree/main/scripts/stability>

- 腳本 zip（直接下載）：<../assets/scripts/stability/C15806945_WiFi_radio_enable_disable_longrun.zip>


### Export script zip（API）

> 說明：`script_id` 可能因 delete/import 變動；建議以 `suite+name` 查到 id 後再 export。

```bash
export CONTROL_PC_IP="172.14.1.140"
export CHARTER_BASE="http://${CONTROL_PC_IP}:5173"
export SUITE="stability"
export NAME="C15806945_WiFi_radio_enable_disable_longrun"

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
- Suite: **stability**
- Script ID（可能因 delete/import 變動）：`11F_140=5117`
- 版本（manifest version）：`v1-wifi_radio_longrun_sshfix_v6`
- Entrypoint：`cycle_wrapper.py:run`

> 本頁由工具依 11F_140 最新 export zip 自動產生/更新（2026-03-10）。

## 一句話說明

- Wi‑Fi/SSID 連線與 radio 行為驗證


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


??? note "manifest.yaml（流程參數完整；帳密/API key 已遮蔽）"

    ```yaml
    name: C15806945_WiFi_radio_enable_disable_longrun
    suite: stability
    version: v1-wifi_radio_longrun_sshfix_v6
    entrypoint: cycle_wrapper.py:run
    env:
      CYCLES: '1'
      CYCLE_INTERVAL: 60
      STOP_ON_FAIL: 1
      ORIGINAL_ENTRY: main_impl_orig.py:run
      TOOLS_PATH: /home/da40/charter/tools
      METRICS_TOOL: /home/da40/charter/tools/cpe_metrics_agent_serial.py
      NODE_ID_MAX_RETRIES: 30
      NODE_ID_RETRY_INTERVAL_SEC: 2
      CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
      CPE_BAUD: 115200
      CPE_USER: root
      CPE_PASSWORD: 'null'
      NOC_BASE: https://piranha-int.tau.dev-charter.net
      CUSTOMER_ID: 682d4e5179b80027cd6fb27e
      NOC_PROFILE: SPECTRUM_INT
      PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
      SSH_USER: operator
      SSH_PASSWORD: <fill>
      SSH_TIMEOUT_MIN: 120
      SSH_REENABLE_EACH_CYCLE: 0
      SSH_HOST_LAN: 192.168.1.1
      HEALTH_WAIT_SEC: '60'
      WAN_SSH_REQUIRED: 1
      LAN_SSH_REQUIRED: 1
      CPE_SSH_TOOL: /home/da40/charter/tools/cpe_ssh.py
      SSH_TOOL_TIMEOUT: 15
      USE_CLOUD_SSH: '1'
      CPE_LOG_TIMEOUT_SEC: '240'
      SSH_ACTION: enable
      ENABLE_NOC_API_TESTS: 1
      SPEEDTEST_WAIT_SEC: 90
      ENABLE_SPEEDTEST: 0
      ENABLE_WIFI_TEST: 1
      WIFI_TOGGLE_HOLD_SEC: '0'
      ENABLE_LTE_TEST: 0
      ENABLE_SSH_FLOW: '1'
      SPEEDTEST_MAX_TRIES: 3
      SPEEDTEST_INTERVAL_SEC: 10
      INTERNET_CHECK_MAX_RETRIES: '10'
      INTERNET_CHECK_INTERVAL_SEC: '3'
      ENABLE_DNS_CHECK: 0
      TARGET: www.google.com
      SECOND: cloudflare.com
      EXPECT_A_MIN: 1
      EXPECT_AAAA_MIN: 1
      RETRIES: 3
      INTERVAL_SEC: 3
      DNS_SSH_TIMEOUT_SEC: 30
    ```
