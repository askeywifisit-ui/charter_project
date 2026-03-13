# A2435637_Continuously_executing_FactoryReset



---

## 來源與下載

- GitHub scripts 目錄：<https://github.com/askeywifisit-ui/charter_project/tree/main/scripts/stability>

- 腳本 zip（直接下載）：<../assets/scripts/stability/A2435637_Continuously_executing_FactoryReset.zip>


### Export script zip（API）

> 說明：`script_id` 可能因 delete/import 變動；建議以 `suite+name` 查到 id 後再 export。

```bash
export CONTROL_PC_IP="172.14.1.140"
export CHARTER_BASE="http://${CONTROL_PC_IP}:5173"
export SUITE="stability"
export NAME="A2435637_Continuously_executing_FactoryReset"

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
- Script ID（可能因 delete/import 變動）：`11F_140=5217`
- 版本（manifest version）：`v15-no-console-lock-cycle-index-fix-pdu-recovery-sshprobe-harden`
- Entrypoint：`cycle_wrapper.py:run`

> 本頁由工具依 11F_140 最新 export zip 自動產生/更新（2026-03-10）。

## 一句話說明

- Factory Reset/回復出廠驗證


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
    name: A2435637_Continuously_executing_FactoryReset
    suite: stability
    version: v15-no-console-lock-cycle-index-fix-pdu-recovery-sshprobe-harden
    entrypoint: cycle_wrapper.py:run
    env:
      CYCLES: '1'
      CYCLE_INTERVAL: '70'
      STOP_ON_FAIL: '1'
      ORIGINAL_ENTRY: main_impl.py:run
      TOOLS_PATH: /home/da40/charter/tools
      TOOLS_PYTHON: python3
      CUSTOMER_ID: 682d4e5179b80027cd6fb27e
      PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
      NOC_PROFILE: SPECTRUM_INT
      SERIAL_METRICS: /home/da40/charter/tools/cpe_metrics_agent_serial.py
      CPE_IP: 192.168.1.1
      SSH_USER: operator
      SSH_PASSWORD: <fill>
      CPE_BAUD: '115200'
      PRECOND_SET_WIFI: '1'
      TEST_SSID: FACTORY_2F_TEST
      TEST_PSK: 12345678
      PRECOND_WIFI_CONFIG_SET_TIMEOUT_SEC: '60'
      PRECOND_WIFI_CONFIG_SET_RETRIES: '3'
      PRECOND_WIFI_CONFIG_SET_RETRY_INTERVAL_SEC: '3'
      DEFAULT_SSID_PREFIX: SpectrumSetup-
      READY_RETRIES: '120'
      READY_INTERVAL_SEC: '5'
      RESET_WAIT_SEC: '90'
      WAIT_SERIAL_NODE_ID: '0'
      SERIAL_NODE_ID_RETRIES: '30'
      SERIAL_NODE_ID_INTERVAL_SEC: '5'
      SERIAL_NODE_ID_TIMEOUT_SEC: '30'
      RESET_MUTE_SECS: '60'
      RESET_MUTE_WITH_LOCK: '0'
      ENABLE_BASELINE_HEALTH: '1'
      PDU_IP: 172.14.1.135
      PDU_RESET_WAIT_SEC: '120'
      NODE_ID_MAX_RETRIES: 10
    ```
