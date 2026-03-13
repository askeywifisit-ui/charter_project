# C15807139_SSH_should_be_allowed_to_WAN_from_operator_facing_client



---

## 來源與下載

- GitHub 文件來源：<https://github.com/askeywifisit-ui/charter_project/blob/main/docs/charter_site/docs/test_suites/sanity/C15807139_SSH_should_be_allowed_to_WAN_from_operator_facing_client.md>

- 腳本 zip（直接下載）：<../assets/scripts/sanity/C15807139_SSH_should_be_allowed_to_WAN_from_operator_facing_client.zip>


### Export script zip（API）

> 說明：`script_id` 可能因 delete/import 變動；建議以 `suite+name` 查到 id 後再 export。

```bash
export CONTROL_PC_IP="172.14.1.140"
export CHARTER_BASE="http://${CONTROL_PC_IP}:5173"
export SUITE="sanity"
export NAME="C15807139_SSH_should_be_allowed_to_WAN_from_operator_facing_client"

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
- Script ID（可能因 delete/import 變動）：`11F_140=5178`
- 版本（manifest version）：`v8`
- Entrypoint：`cycle_wrapper.py:run`

> 本頁由工具依 11F_140 最新 export zip 自動產生/更新（2026-03-10）。

## 一句話說明

- SSH 行為/權限驗證（allow/deny/port/session/credential 等）


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
    name: C15807139_SSH_should_be_allowed_to_WAN_from_operator_facing_client
    suite: sanity
    version: v8
    entrypoint: cycle_wrapper.py:run
    env:
      IPV4_TO_IPV6_SLEEP_SEC: 3
      CYCLES: '1'
      CYCLE_INTERVAL: '70'
      STOP_ON_FAIL: 1
      ORIGINAL_ENTRY: main_impl_orig.py:run
      TOOLS_PATH: /home/da40/charter/tools
      CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
      CPE_SSH_TOOL: /home/da40/charter/tools/cpe_ssh.py
      NODE_ID_USE_SERIAL: 0
      CUSTOMER_ID: 682d4e5179b80027cd6fb27e
      NOC_PROFILE: SPECTRUM_INT
      PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
      SSH_USER: operator
      SSH_PASSWORD: <fill>
      SSH_TIMEOUT_MIN: 120
      SSH_HOST_LAN: 192.168.1.1
      AUTO_SSH_ENABLE: 1
      REQUIRE_SSH_READY: 1
      SSH_ENABLE_ATTEMPTS: 2
      SSH_READY_WAIT_SEC: 30
      SSH_TOOL_TIMEOUT: 15
      ENABLE_SSH_FLOW: 1
      LAN_SSH_REQUIRED: 1
      WAN_SSH_TIMEOUT_SEC: 30
      SSH_ENABLE_WAIT_SEC: 10
      WAN_SSH_READY_RETRIES: 10
      WAN_SSH_READY_INTERVAL_SEC: 3
      WAN_SSH_READY_TIMEOUT_SEC: 3
      WAN_SSH_LOGIN_RETRIES: 8
      WAN_SSH_LOGIN_INTERVAL_SEC: 5
      WAN_SSH_LOGIN_TIMEOUT_SEC: 10
      ENABLE_IPV6: auto
      IPV6_REQUIRED: 1
      SKIP_IPV6: 0
      CPE_LAN_IFACE: br-home
      CLIENT_WAN_IFACE: auto
      CLIENT_LAN_IFACE: auto
      WAN_SSH_BIND_SRC4: auto
      WAN_SSH_BIND_SRC6: auto
      WAN_SSH_BIND_IFACE: auto
      REQUIRE_OPERATOR_FACING: 0
      CPE_READY_CHECK: '1'
      CPE_INFO_STATUS_CMD: cpe_info -status
      CPE_READY_MAX_RETRIES: '5'
      CPE_READY_RETRY_INTERVAL_SEC: '3'
      CPE_READY_REQUIRE_CLOUD: '1'
      PDU_RESET_ON_NOT_READY: '1'
      PDU_RESET_ACTION: reset
      PDU_RESET_WAIT_SEC: '120'
      CPE_READY_TIMEOUT_SEC: '60'
      NODE_ID_MAX_RETRIES: 10
    ```
