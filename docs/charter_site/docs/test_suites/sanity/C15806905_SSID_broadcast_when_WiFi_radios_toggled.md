# C15806905_SSID_broadcast_when_WiFi_radios_toggled



---

## 來源與下載

- GitHub scripts 目錄：<https://github.com/askeywifisit-ui/charter_project/tree/main/scripts/sanity>

- 腳本 zip（直接下載）：<../assets/scripts/sanity/C15806905_SSID_broadcast_when_WiFi_radios_toggled.zip>


### Export script zip（API）

> 說明：`script_id` 可能因 delete/import 變動；建議以 `suite+name` 查到 id 後再 export。

```bash
export CONTROL_PC_IP="172.14.1.140"
export CHARTER_BASE="http://${CONTROL_PC_IP}:5173"
export SUITE="sanity"
export NAME="C15806905_SSID_broadcast_when_WiFi_radios_toggled"

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
- Script ID（可能因 delete/import 變動）：`11F_140=5204`
- 版本（manifest version）：`v16_platform_hint_manifest_fallback_warn`
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
- `WIFI_IFACE`: `wlx6cb0ce1ff230`


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
      WIFI_IFACE: wlx6cb0ce1ff230
    ```


??? note "manifest.yaml（流程參數完整；帳密/API key 已遮蔽）"

    ```yaml
    name: C15806905_SSID_broadcast_when_WiFi_radios_toggled
    suite: sanity
    version: v16_platform_hint_manifest_fallback_warn
    entrypoint: cycle_wrapper.py:run
    env:
      CYCLES: '1'
      CYCLE_INTERVAL: '20'
      STOP_ON_FAIL: '1'
      ORIGINAL_ENTRY: main_impl_orig.py:run
      TOOLS_PATH: /home/da40/charter/tools
      CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
      CPE_SSH_TOOL: /home/da40/charter/tools/cpe_ssh.py
      NODE_ID_READY_CHECK: '1'
      NODE_ID_MAX_RETRIES: '10'
      NODE_ID_RETRY_INTERVAL_SEC: '5'
      CPE_READY_CHECK: '1'
      CPE_INFO_STATUS_CMD: cpe_info -status
      CPE_READY_MAX_RETRIES: '10'
      CPE_READY_RETRY_INTERVAL_SEC: '3'
      CPE_READY_REQUIRE_CLOUD: '1'
      PDU_RESET_ON_NOT_READY: '1'
      PDU_RESET_ACTION: reset
      PDU_RESET_TIMEOUT_SEC: '120'
      PDU_RESET_WAIT_SEC: '120'
      POST_PDU_STABILIZE_SEC: '40'
      ENABLE_SSH_FLOW: '1'
      SSH_ACTION: enable
      REQUIRE_SSH_READY: '1'
      SSH_READY_RETRY: '40'
      SSH_READY_WAIT_SEC: '3'
      SSH_READY_CMD: health
      NOC_BASE: https://piranha-int.tau.dev-charter.net
      PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
      NOC_PROFILE: SPECTRUM_INT
      CUSTOMER_ID: 682d4e5179b80027cd6fb27e
      NOC_EMAIL: ''
      NOC_PASSWORD: ''
      BEARER: <fill>
      INSECURE: '0'
      NOC_TIMEOUT_SEC: '30'
      NOC_RETRIES: '3'
      SSH_HOST_LAN: 192.168.1.1
      SSH_USER: operator
      SSH_PASSWORD: <fill>
      SSH_TIMEOUT_MIN: '120'
      CPE_USER: operator
      CPE_PASSWORD: <fill>
      CPE_SSH_TIMEOUT_SEC: '25'
      SSH_TOOL_TIMEOUT: '25'
      WIFI_IFACE: wlx6cb0ce1ff230
      WIFI_BAND: ''
      WIFI_CRED_PREFER: current
      WIFI_DHCP_TIMEOUT_SEC: '35'
      WIFI_IWD_TIMEOUT_SEC: '90'
      WIFI_POST_ENABLE_GRACE_SEC: '6'
      WIFI_CONNECT_RETRIES: '3'
      WIFI_CONNECT_RETRY_WAIT_SEC: '3'
      WIFI_TAKEOVER_ON_RETRY: '1'
      WIFI_FALLBACK_ANY_BAND: '1'
      WIFI_SSID: ''
      WIFI_PSK: ''
      WIFI_PSK_ENV: ''
      WIFI_NO_MAIN_DEFAULT: '1'
      WIFI_PBR_TABLE: '101'
      WIFI_PBR_FROM_IP: '0'
      WIFI_NOC_STATE_TIMEOUT_SEC: '180'
      WIFI_VIF_STATE_TIMEOUT_SEC: '180'
      WIFI_SCAN_TIMEOUT_SEC: '300'
      POLL_INTERVAL_SEC: '5'
      REQUIRE_SSH_VIF_OFF: '0'
      PING_TARGET: 192.168.1.1
      PING_COUNT: '2'
    ```
