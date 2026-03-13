# C15806953_Router_resolves_the_DNS_queries_using_IPv4



---

## 來源與下載

- GitHub 文件來源：<https://github.com/askeywifisit-ui/charter_project/blob/main/docs/charter_site/docs/test_suites/sanity/C15806953_Router_resolves_the_DNS_queries_using_IPv4.md>

- 腳本 zip（直接下載）：<../assets/scripts/sanity/C15806953_Router_resolves_the_DNS_queries_using_IPv4.zip>


### Export script zip（API）

> 說明：`script_id` 可能因 delete/import 變動；建議以 `suite+name` 查到 id 後再 export。

```bash
export CONTROL_PC_IP="172.14.1.140"
export CHARTER_BASE="http://${CONTROL_PC_IP}:5173"
export SUITE="sanity"
export NAME="C15806953_Router_resolves_the_DNS_queries_using_IPv4"

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
- Script ID（可能因 delete/import 變動）：`11F_140=5168`
- 版本（manifest version）：`v2-DNS_queries_IPv4`
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
    name: C15806953_Router_resolves_the_DNS_queries_using_IPv4
    suite: sanity
    version: v2-DNS_queries_IPv4
    entrypoint: cycle_wrapper.py:run
    env:
      CYCLES: '1'
      CYCLE_INTERVAL: 70
      STOP_ON_FAIL: 1
      ORIGINAL_ENTRY: main_impl_orig.py:run
      TOOLS_PATH: /home/da40/charter/tools
      METRICS_TOOL: /home/da40/charter/tools/cpe_metrics_agent_serial.py
      CPE_BAUD: '115200'
      CPE_USER: root
      CPE_PASSWORD: ''
      CPE_IFACE: br-wan
      NOC_BASE: https://piranha-int.tau.dev-charter.net
      NOC_EMAIL: <fill>
      NOC_PASSWORD: <fill>
      CUSTOMER_ID: 682d4e5179b80027cd6fb27e
      BEARER: <fill>
      INSECURE: 0
      API_BASE: http://127.0.0.1:8080
      DISABLE_INTERNAL_LOGPULL: '1'
      USE_CLOUD_SSH: '1'
      CPE_LOG_TIMEOUT_SEC: '240'
      NOC_PROFILE: SPECTRUM_INT
      PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
      ENABLE_SSH_FLOW: 1
      SSH_ENABLE_RETRIES: 3
      SSH_SCAN_TIMEOUT_SEC: 30
      SSH_USER: operator
      SSH_PASSWORD: <fill>
      SSH_TIMEOUT_MIN: '120'
      CPE_HEALTH_HOST: 192.168.1.1
      CPE_HEALTH_PORT: '22'
      SSH_PORT_CHECK_TIMEOUT: '3'
      ENABLE_SPEEDTEST: 0
      ENABLE_WIFI_TEST: 0
      ENABLE_LTE_TEST: 0
      ENABLE_HEALTH_CHECK: 0
      ENABLE_DNS_CHECK: 1
      TARGET: www.google.com
      SECOND: www.o2.de
      EXPECT_A_MIN: 1
      EXPECT_AAAA_MIN: 1
      RETRIES: 3
      INTERVAL_SEC: 3
      DNS_SSH_TIMEOUT_SEC: 30
      DNS_INVALID_IPS: 172.14.1.1, 127.0.0.53,223.255.255.1, 223.255.255.1
      DEBUG_DNS: '0'
      DEBUG_SHOW_CMD: '0'
      SAVE_DNS_RESULTS: '1'
      DNS_RESULTS_FILE: dns_results.json
      NODE_ID_MAX_TRIES: 3
      NODE_ID_INTERVAL_SEC: 2
      NODE_ID_CMD_TIMEOUT_SEC: 15
    ```
