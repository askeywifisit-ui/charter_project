# C15807061_WAN_IPv6_Connectivity



---

## 來源與下載

- GitHub scripts 目錄：<https://github.com/askeywifisit-ui/charter_project/tree/main/scripts/sanity>

- 腳本 zip（直接下載）：<../assets/scripts/sanity/C15807061_WAN_IPv6_Connectivity.zip>


### Export script zip（API）

> 說明：`script_id` 可能因 delete/import 變動；建議以 `suite+name` 查到 id 後再 export。

```bash
export CONTROL_PC_IP="172.14.1.140"
export CHARTER_BASE="http://${CONTROL_PC_IP}:5173"
export SUITE="sanity"
export NAME="C15807061_WAN_IPv6_Connectivity"

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
- Script ID（可能因 delete/import 變動）：`11F_140=5170`
- 版本（manifest version）：`v1-WAN_IPv6_Connectivity`
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
    name: C15807061_WAN_IPv6_Connectivity
    suite: sanity
    version: v1-WAN_IPv6_Connectivity
    entrypoint: cycle_wrapper.py:run
    env:
      SERIAL_DIAG_ENABLED: '0'
      SKIP_ON_NO_IPV6: '0'
      CYCLES: '1'
      CYCLE_INTERVAL: '60'
      STOP_ON_FAIL: '0'
      ORIGINAL_ENTRY: main_impl.py:run
      CPE_READY_CHECK: '1'
      CPE_INFO_STATUS_CMD: cpe_info -status
      CPE_READY_MAX_RETRIES: '5'
      CPE_READY_RETRY_INTERVAL_SEC: '3'
      CPE_READY_REQUIRE_CLOUD: '1'
      PDU_RESET_ON_NOT_READY: '1'
      PDU_RESET_SCRIPT: /home/da40/charter/tools/pdu_outlet2.py
      PDU_RESET_ACTION: reset
      PDU_RESET_WAIT_SEC: '120'
      PDU_RESET_TIMEOUT_SEC: '600'
      TOOLS_PATH: /home/da40/charter/tools
      TOOLS_PYTHON: python3
      WAN_IPV6_METHOD: ssh
      WAN_IPV6_RETRIES: '12'
      WAN_IPV6_WAIT_MS: '700'
      REQUIRE_PREFIXLEN_128: '0'
      ENABLE_SSH_PRECOND: '1'
      SSH_PRECOND_CACHE_ENABLED: '1'
      SSH_PRECOND_CACHE_TTL_SEC: '600'
      CPE_IP: 192.168.1.1
      SSH_USER: operator
      SSH_PASSWORD: <fill>
      CUSTOMER_ID: 682d4e5179b80027cd6fb27e
      NOC_PROFILE: SPECTRUM_INT
      PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
      CPE_BAUD: '115200'
      CPE_USER: root
      CPE_PASSWORD: ''
      CPE_IFACE: br-wan
      API_BASE: http://127.0.0.1:8080
      SERIAL_SETTLE_MS: '800'
      STEP_WAIT_BEFORE_MS: '100'
      STEP_WAIT_AFTER_MS: '100'
      WAIT_AFTER_STEP1_MS: '200'
      WAIT_AFTER_STEP2_MS: '200'
      WAIT_AFTER_STEP3_MS: '1200'
      CPE_PING6_1: 2001:4860:4860::8888
      CPE_PING6_2: 2606:4700:4700::1111
      PING_METHOD: ssh
      SSH_PING_TIMEOUT_SEC: '15'
      SSH_PING_COUNT: '1'
      METRICS_METHOD: ssh
      SSH_METRICS_TIMEOUT_SEC: '25'
      RETRIES: '3'
      INTERVAL_SEC: '1'
      SHOW_METRICS: '1'
      ECHO_METRICS: '1'
      ECHO_MAX_LINES: '12'
      DEBUG_METRICS: '0'
      CPE_INFO_BIN: /home/da40/charter/tools/cpe_info
      NODE_ID_MAX_RETRIES: 10
    ```
