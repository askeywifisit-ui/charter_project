# C15807949_IP_reservation_for_WLAN_connected_clients



---

## 來源與下載

- GitHub 文件來源：<https://github.com/askeywifisit-ui/charter_project/blob/main/docs/charter_site/docs/test_suites/sanity/C15807949_IP_reservation_for_WLAN_connected_clients.md>

- GitHub scripts（zip）：<https://raw.githubusercontent.com/askeywifisit-ui/charter_project/main/scripts/sanity/C15807949_IP_reservation_for_WLAN_connected_clients.zip>
  - 目錄：<https://github.com/askeywifisit-ui/charter_project/blob/main/scripts/sanity>

### Export script zip（API）

> 說明：`script_id` 可能因 delete/import 變動；建議以 `suite+name` 查到 id 後再 export。

```bash
export CONTROL_PC_IP="172.14.1.140"
export CHARTER_BASE="http://${CONTROL_PC_IP}:5173"
export SUITE="sanity"
export NAME="C15807949_IP_reservation_for_WLAN_connected_clients"

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
- Script ID（可能因 delete/import 變動）：`11F_140=5210`
- 版本（manifest version）：`v1-wifi-noc-dhcp-resv-reconnect-delete-cpe-gate-noc-evidence`
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
- `CPE_HOST`: `192.168.1.1`
- `SSH_PASSWORD`: `<fill>`
- `WIFI_IFACE`: `wlx6cb0ce1ff230`
- `PING_IFACE`: `eno2`
- `CPE_DEV`: `/dev/ttyUSB0`
- `TEST_PROFILE`: `lab`


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
      WIFI_IFACE: wlx6cb0ce1ff230
      PING_IFACE: eno2
      CPE_DEV: /dev/ttyUSB0
      TEST_PROFILE: lab
    ```


??? note "manifest.yaml（流程參數完整；帳密/API key 已遮蔽）"

    ```yaml
    name: C15807949_IP_reservation_for_WLAN_connected_clients
    suite: sanity
    version: v1-wifi-noc-dhcp-resv-reconnect-delete-cpe-gate-noc-evidence
    entrypoint: cycle_wrapper.py:run
    env:
      TEST_NAME: C15807949_IP_reservation_for_WLAN_connected_clients
      CYCLE_TOTAL: '1'
      CYCLE_INTERVAL_SEC: '60'
      STOP_ON_FAIL: '1'
      CYCLES: '1'
      CYCLE_INTERVAL: '70'
      ORIGINAL_ENTRY: main_impl.py:run
      TOOLS_PATH: /home/da40/charter/tools
      WIFI_IWD_TOOL: /home/da40/charter/tools/wifi_iwd.py
      WIFI_NM_TOOL: /home/da40/charter/tools/wifi_nm.py
      NOC_PROFILE: SPECTRUM_INT
      PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
      CUSTOMER_ID: 682d4e5179b80027cd6fb27e
      CPE_HOST: 192.168.1.1
      CPE_SSH_USER: operator
      SSH_PASSWORD: <fill>
      CPE_SSH_PORT: '22'
      CPE_SSH_TIMEOUT_SEC: '30'
      SSH_READY_CMD: uptime
      SSH_SCAN_TIMEOUT_SEC: '30'
      SSH_SCAN_INTERVAL_SEC: '2'
      SSH_PASSWORD_DEFAULT: <fill>
      SSH_ENABLE_RETRIES: '2'
      WAIT_AFTER_SSH_ENABLE_SEC: '60'
      PDU_SCRIPT: /home/da40/charter/tools/pdu_outlet1.py
      PDU_OUTLET_ID: '1'
      POST_PDU_STABILIZE_SEC: '40'
      CLOUD_READY_TIMEOUT_SEC: '30'
      CLOUD_READY_INTERVAL_SEC: '3'
      NODE_ID_MAX_RETRIES: '10'
      NODE_ID_RETRY_INTERVAL_SEC: '3'
      SSH_ENABLE_ATTEMPTS: '2'
      SSH_ENABLE_WAIT_SEC: '20'
      WIFI_IFACE: wlx6cb0ce1ff230
      WIFI_METHOD: auto
      WIFI_BAND: 5g
      WIFI_CRED_PREFER: current
      WIFI_TIMEOUT_SEC: '45'
      WIFI_NM_RETRIES: '2'
      WIFI_RECONNECT_WAIT_SEC: '2'
      WIFI_DISCONNECT_ON_EXIT: '1'
      WIFI_FORCE_STATIC_MAC: '0'
      WIFI_TEST_MAC: ''
      WIFI_PING_ROUTER_ENABLE: '1'
      WIFI_PING_ROUTER: 192.168.1.1
      WIFI_PING_INTERNET: '0'
      WIFI_PING_TARGET: www.google.com
      WIFI_PING_COUNT: '3'
      WIFI_PING_TIMEOUT_SEC: '5'
      TEST_HOSTNAME: wifi_test0
      TEST_RESERVED_IP: 192.168.1.225
      ALLOW_SAME_IP: '0'
      CLEAR_CONFLICTING_IP_RESERVATION: '1'
      CLEAR_ALL_NOC_DHCP_RESERVATIONS: '0'
      CLEAR_ALL_NOC_DHCP_RESERVATIONS_HOSTNAME_PREFIX: ''
      AUTO_PICK_FREE_IP: '1'
      WAIT_AFTER_RESERVATION_SET_SEC: '5'
      DELETE_RESERVATION_AT_END: '1'
      CLEANUP_ON_FAIL: '1'
      RESERVED_ABSENT_TIMEOUT_SEC: '60'
      RESERVED_ABSENT_INTERVAL_SEC: '5'
      DHCP_DUMP_RETRIES: '3'
      DHCP_DUMP_RETRY_WAIT_SEC: '2'
      LEASE_WAIT_TIMEOUT_SEC: '60'
      LEASE_WAIT_INTERVAL_SEC: '5'
      TEST_PROFILE: lab
      CPE_DEV: /dev/ttyUSB0
      PING_IFACE: eno2
    ```
