# C15807946_Delete_DHCP_Reservation



---

## 來源與下載

- GitHub scripts 目錄：<https://github.com/askeywifisit-ui/charter_project/tree/main/scripts/sanity>


### Export script zip（API）

> 說明：`script_id` 可能因 delete/import 變動；建議以 `suite+name` 查到 id 後再 export。

```bash
export CONTROL_PC_IP="172.14.1.140"
export CHARTER_BASE="http://${CONTROL_PC_IP}:5173"
export SUITE="sanity"
export NAME="C15807946_Delete_DHCP_Reservation"

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
- Script ID（可能因 delete/import 變動）：`11F_140=5216`
- 版本（manifest version）：`v1-cpe-gate-noc-evidence-only-precond-baseline-ipinuse-retry-customersafe`
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
    name: C15807946_Delete_DHCP_Reservation
    suite: sanity
    version: v1-cpe-gate-noc-evidence-only-precond-baseline-ipinuse-retry-customersafe
    entrypoint: cycle_wrapper.py:run
    env:
      TEST_NAME: C15807946_Delete_DHCP_Reservation
      CYCLE_INTERVAL_SEC: '60'
      STOP_ON_FAIL: '1'
      CYCLES: '1'
      CYCLE_INTERVAL: '70'
      TOOLS_PATH: /home/da40/charter/tools
      NOC_PROFILE: SPECTRUM_INT
      PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
      CUSTOMER_ID: 682d4e5179b80027cd6fb27e
      CPE_HOST: 192.168.1.1
      CPE_SSH_USER: operator
      SSH_PASSWORD: <fill>
      SSH_READY_CMD: uptime
      CPE_SSH_PORT: '22'
      SSH_SCAN_TIMEOUT_SEC: '30'
      SSH_SCAN_INTERVAL_SEC: '2'
      CPE_SSH_TIMEOUT_SEC: '30'
      SSH_PASSWORD_DEFAULT: <fill>
      SSH_ENABLE_RETRIES: '2'
      WAIT_AFTER_SSH_ENABLE_SEC: '60'
      POST_PDU_STABILIZE_SEC: '40'
      SERIAL_MUTE_SEC: '60'
      CLOUD_READY_TIMEOUT_SEC: '30'
      CLOUD_READY_INTERVAL_SEC: '3'
      NODE_ID_MAX_RETRIES: '10'
      NODE_ID_RETRY_INTERVAL_SEC: '3'
      SSH_ENABLE_ATTEMPTS: '2'
      SSH_ENABLE_WAIT_SEC: '20'
      LAN_TEST_IFACE: auto
      LAN_TEST_MAC: ''
      LAN_PING_TARGET: google.com
      LAN_RENEW_TIMEOUT_SEC: '120'
      TEST_HOSTNAME: lan_test0
      TEST_RESERVED_IP: 192.168.1.225
      CLEAR_CONFLICTING_IP_RESERVATION: '1'
      CLEAR_ALL_NOC_DHCP_RESERVATIONS: '0'
      CLEAR_ALL_NOC_DHCP_RESERVATIONS_HOSTNAME_PREFIX: lan_test
      AUTO_PICK_FREE_IP: '1'
      IP_IN_USE_RETRY_MAX: '10'
      DHCP_DUMP_RETRIES: '8'
      DHCP_DUMP_RETRY_WAIT_SEC: '5'
      LEASE_WAIT_TIMEOUT_SEC: '180'
      LEASE_WAIT_INTERVAL_SEC: '10'
      DELETE_VERIFY_TIMEOUT_SEC: '240'
      DELETE_VERIFY_INTERVAL_SEC: '10'
      EXPECT_NO_NOC_RESERVATIONS_AFTER_DELETE: '1'
      EXPECT_NO_CPE_RESERVATIONS_AFTER_DELETE: '1'
      LAN_RENEW_AFTER_DELETE: '1'
      LAN_RENEW_AFTER_DELETE_ATTEMPTS: '2'
    ```
