# A2844344_Continuously_executing_reboot



---

## 來源與下載

- GitHub scripts 目錄：<https://github.com/askeywifisit-ui/charter_project/tree/main/scripts/stability>


### Export script zip（API）

> 說明：`script_id` 可能因 delete/import 變動；建議以 `suite+name` 查到 id 後再 export。

```bash
export CONTROL_PC_IP="172.14.1.140"
export CHARTER_BASE="http://${CONTROL_PC_IP}:5173"
export SUITE="stability"
export NAME="A2844344_Continuously_executing_reboot"

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
- Script ID（可能因 delete/import 變動）：`11F_140=5116`
- 版本（manifest version）：`v2-professional-noc_profile-only-nodeid-cpeinfo`
- Entrypoint：`cycle_wrapper.py:run`

> 本頁由工具依 11F_140 最新 export zip 自動產生/更新（2026-03-10）。

## 一句話說明

- reboot/多次重啟壓力驗證


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
    name: A2844344_Continuously_executing_reboot
    suite: stability
    version: v2-professional-noc_profile-only-nodeid-cpeinfo
    entrypoint: cycle_wrapper.py:run
    env:
      CYCLES: '1'
      CYCLE_INTERVAL: '90'
      STOP_ON_FAIL: 0
      ORIGINAL_ENTRY: main_impl.py:run
      TOOLS_PATH: /home/da40/charter/tools
      REBOOT_MUTE_SECS: 60
      REBOOT_MUTE_WITH_LOCK: 0
      SSH_PASSWORD: <fill>
      NOC_BASE: https://piranha-int.tau.dev-charter.net
      NOC_PROFILE: SPECTRUM_INT
      PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
      CUSTOMER_ID: 682d4e5179b80027cd6fb27e
      BEARER: <fill>
      INSECURE: 0
      LOCATION_ID: ''
      CPE_BAUD: 115200
      CPE_USER: root
      CPE_PASSWORD: null
      POST_REBOOT_STATUS_WAIT_SEC: 120
      ENABLE_VERSION_GUARD: 1
      CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
      CPE_INFO_FWV_ARGS: -f "FW Version" --value
      ENABLE_SSH_PRE_SCAN: 1
      SSH_TIMEOUT_MIN: 120
      WAIT_AFTER_SSH_ENABLE_SEC: 60
      SSH_HOST_LAN: 192.168.1.1
      SSH_USER: operator
      CPE_SSH_TOOL: /home/da40/charter/tools/cpe_ssh.py
      SSH_TOOL_TIMEOUT: 15
      CPE_UPTIME_CMD: uptime
      SSH_SCAN_TIMEOUT_SEC: 60
      SSH_SCAN_INTERVAL_SEC: 2
      SSH_SCAN_PER_TRY_TIMEOUT_SEC: 2
      ENABLE_UPTIME_LOCAL_CHECK: 1
      ENABLE_UPTIME_COMPARE: 1
      NOC_API_CLI: /home/da40/charter/tools/noc_api_cli.py
      NOC_API_CLI_TIMEOUT_SEC: 30
      CLOUD_UPTIME_MODE: bootAt
      UPTIME_TOLERANCE_SEC: 120
      CLOUD_STATIC_LAG_SEC: 0
      FAIL_PULL_ENABLED: 1
      FAIL_WAIT_BEFORE_PULL_SEC: 60
      FAIL_PULL_SSH_ENABLED: 1
      FAIL_PULL_SSH_SCAN_TIMEOUT_SEC: 60
      FAIL_PULL_CLOUD_ENABLED: 1
      FAIL_AFTER_PULL_DELAY_SEC: 5
      FAIL_PULL_TIMEOUT_SEC: 300
      FAIL_PULL_LATEST_DIR: /tmp/logpull
      FAIL_PULL_PATTERN: '*.tar.gz'
      FAIL_PULL_DELETE_REMOTE: 0
      ENABLE_PARTITION_GUARD: 0
      PARTITION_FIELD: ''
      DEBUG: 1
    ```
