# C15807173_Test_Upnp_discovery



---

## 來源與下載

- GitHub scripts 目錄：<https://github.com/askeywifisit-ui/charter_project/tree/main/scripts/sanity>

- 腳本 zip（直接下載）：<../assets/scripts/sanity/C15807173_Test_Upnp_discovery.zip>


### Export script zip（API）

> 說明：`script_id` 可能因 delete/import 變動；建議以 `suite+name` 查到 id 後再 export。

```bash
export CONTROL_PC_IP="172.14.1.140"
export CHARTER_BASE="http://${CONTROL_PC_IP}:5173"
export SUITE="sanity"
export NAME="C15807173_Test_Upnp_discovery"

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
- Script ID（可能因 delete/import 變動）：`11F_140=5215`
- 版本（manifest version）：`v1-upnp-ready-wait-retry-soap-fault`
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
    name: C15807173_Test_Upnp_discovery
    suite: sanity
    version: v1-upnp-ready-wait-retry-soap-fault
    entrypoint: cycle_wrapper.py:run
    env:
      CYCLES: '1'
      CYCLE_INTERVAL: '30'
      STOP_ON_FAIL: 1
      ORIGINAL_ENTRY: main_impl_orig.py:run
      TOOLS_PATH: /home/da40/charter/tools
      METRICS_TOOL: /home/da40/charter/tools/cpe_metrics_agent_serial.py
      CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
      CPE_SSH_TOOL: /home/da40/charter/tools/cpe_ssh.py
      USE_SERIAL_NODEID: '0'
      CPE_BAUD: 115200
      CPE_USER: root
      CPE_PASSWORD: null
      NOC_BASE: https://piranha-int.tau.dev-charter.net
      PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
      NOC_PROFILE: SPECTRUM_INT
      CUSTOMER_ID: 682d4e5179b80027cd6fb27e
      NOC_EMAIL: ''
      NOC_PASSWORD: ''
      NOC_BEARER: <fill>
      NOC_INSECURE: '0'
      SSH_HOST_LAN: 192.168.1.1
      SSH_USER: operator
      SSH_PASSWORD: <fill>
      SSH_TOOL_TIMEOUT: 20
      SSH_ENABLE_AT_START: '1'
      SSH_TIMEOUT_MIN: '120'
      SSH_PORT_MAX_RETRIES: '10'
      SSH_PORT_INTERVAL_SEC: '3'
      SSH_PORT_CHECK_TIMEOUT: '3'
      SSH_PORT_TIMEOUT_SEC: '240'
      LAN_IFACE: ''
      UPNP_ENABLE_AT_START: '1'
      UPNP_DISABLE_AT_END: '1'
      UPNP_APPLY_WAIT_SEC: '40'
      MINIUPNPD_RETRIES: '8'
      MINIUPNPD_RETRY_INTERVAL_SEC: '5'
      MINIUPNPD_STOP_RETRIES: '10'
      MINIUPNPD_STOP_RETRY_INTERVAL_SEC: '3'
      EXPECT_REBOOT_AFTER_UPNP_ENABLE: '1'
      EXPECT_REBOOT_AFTER_UPNP_DISABLE: '1'
      REBOOT_MUTE_SECS: '120'
      REBOOT_MUTE_WITH_LOCK: '1'
      SERIAL_MUTE_TOOL: /home/da40/charter/tools/serial_mute.py
      CPE_INFO_STATUS_TIMEOUT_SEC: '40'
      CPE_READY_CHECK: '1'
      CPE_READY_MAX_RETRIES: '30'
      CPE_READY_RETRY_INTERVAL_SEC: '6'
      CPE_READY_REQUIRE_CLOUD: '1'
      MINIUPNPD_CMD: ps | grep miniupnpd
      UPNP_IGD_TESTER: /home/da40/charter/tools/upnp_igd_tester.py
      UPNP_IGD_TIMEOUT_SEC: '60'
      UPNP_IGD_TEST_PORT: '54321'
      UPNP_IGD_PROTOCOL: TCP
      REQUIRE_SSDP_MSEARCH_ON: '1'
      REQUIRE_SSDP_MSEARCH_OFF: '1'
      SSDP_MSEARCH_TIMEOUT_SEC: '3'
      SSDP_MSEARCH_RETRIES: '5'
      SSDP_MSEARCH_RETRY_SLEEP_SEC: '5'
      REQUIRE_SSDP_ALIVE: '0'
      REQUIRE_SSDP_BYEBYE: '0'
      TCPDUMP_TIMEOUT_ON_SEC: '180'
      TCPDUMP_TIMEOUT_OFF_SEC: '180'
      TCPDUMP_RETRIES: '3'
      TCPDUMP_RETRY_SLEEP_SEC: '10'
      TCPDUMP_FILTER: udp port 1900
    ```
