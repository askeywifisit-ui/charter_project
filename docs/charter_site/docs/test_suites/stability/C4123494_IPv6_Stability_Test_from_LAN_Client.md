# C4123494_IPv6_Stability_Test_from_LAN_Client



---

## 來源與下載

- GitHub scripts 目錄：<https://github.com/askeywifisit-ui/charter_project/tree/main/scripts/stability>


### Export script zip（API）

> 說明：`script_id` 可能因 delete/import 變動；建議以 `suite+name` 查到 id 後再 export。

```bash
export CONTROL_PC_IP="172.14.1.140"
export CHARTER_BASE="http://${CONTROL_PC_IP}:5173"
export SUITE="stability"
export NAME="C4123494_IPv6_Stability_Test_from_LAN_Client"

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
- Script ID（可能因 delete/import 變動）：`11F_140=5125`
- 版本（manifest version）：`v2-ipv6-lanclient-stability`
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
- `CPE_HOST`: `192.168.1.1`


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
    ```


??? note "manifest.yaml（流程參數完整；帳密/API key 已遮蔽）"

    ```yaml
    name: C4123494_IPv6_Stability_Test_from_LAN_Client
    suite: stability
    version: v2-ipv6-lanclient-stability
    entrypoint: cycle_wrapper.py:run
    env:
      CYCLES: '1'
      CYCLE_INTERVAL: '60'
      STOP_ON_FAIL: '0'
      PRECONDITION_FIRST_CYCLE: '1'
      ORIGINAL_ENTRY: main_impl.py:run
      TOOLS_PATH: /home/da40/charter/tools
      NOC_PROFILE: SPECTRUM_INT
      PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
      CPE_HOST: 192.168.1.1
      CPE_SSH_PORT: '22'
      CPE_SSH_USER: operator
      SSH_PASSWORD_DEFAULT: <fill>
      SSH_SCAN_TIMEOUT_SEC: '30'
      SSH_SCAN_INTERVAL_SEC: '2'
      SSH_ENABLE_RETRIES: '2'
      WAIT_AFTER_SSH_ENABLE_SEC: '60'
      LAN_STACK_WAIT_SEC: '120'
      LAN_IPV6_TARGET: 2001:4860:4860::8888
      LAN_PING_V6_COUNT: '20'
      LAN_PING_V6_DEADLINE_SEC: '20'
      LAN_PING_BACKEND: plain
      LOSS_TRIGGER_PCT: '10'
      CONSEC_FAIL_TRIGGER_N: '3'
      LOGPULL_ON_TRIGGER: '1'
      LOGPULL_LATEST_DIR: /tmp/logpull
      LOGPULL_PATTERN: '*.tar.gz'
      LOG_INCLUDE_TS: '0'
      CUSTOMER_ID: 682d4e5179b80027cd6fb27e
      NODE_ID_MAX_RETRIES: 10
      CPE_WAN_GATEWAY: 223.255.255.1
      PDU_IP: 192.168.168.61
    ```
