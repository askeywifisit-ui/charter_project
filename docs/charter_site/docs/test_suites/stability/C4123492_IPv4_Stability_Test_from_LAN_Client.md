# C4123492_IPv4_Stability_Test_from_LAN_Client

- Suite: **stability**
- Script ID（可能因 delete/import 變動）：`5067`
- 風險等級（對 DUT 影響）：**LOW**

## 目的（Purpose）
- LAN Client（macvlan）IPv4 穩定度測試：反覆 renew/ping（必要時配合 power-cycle recovery）。


## 前置條件（Preconditions）
- CPE/Cloud 需可連線（Internet/Cloud Connected）
- 需要的工具：`/home/da40/charter/tools`（wifi/lan/ssh/pdu 等）

## 測試行為摘要（What it does）
- 建立/維持 LAN client
- 持續 ping/連線檢查（IPv4）
- 紀錄失敗/統計

## 主要參數（manifest env 重要值）
- STOP_ON_FAIL: `'0'`
- CYCLES: `1`
- INTERVAL: `30`

### 需依環境替換（給外部單位）
請參考 **Environment Template**，常見需替換：
- `TOOLS_PATH` / `PROFILES_FILE` / `NOC_PROFILE` / `CUSTOMER_ID`
- `CPE_HOST` / `LAN_PARENT_IFACE` / `WIFI_IFACE` / `PING_IFACE`

## manifest.yaml（節錄）
```yaml
env:
  CYCLES: '1'
  CYCLE_INTERVAL: '30'
  STOP_ON_FAIL: '0'
  ORIGINAL_ENTRY: main_impl.py:run
  PRECONDITION_FIRST_CYCLE: '1'
  TOOLS_PATH: /home/da40/charter/tools
  NOC_PROFILE: SPECTRUM_INT
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
  CPE_HOST: 192.168.1.1
  CPE_SSH_PORT: '22'
  CPE_SSH_USER: operator
  SSH_PASSWORD: <fill>
  SSH_PASSWORD_DEFAULT: <fill>
  REQUIRE_SSH_READY: '1'
  SSH_PROBE_CMD: uptime
  SSH_SCAN_TIMEOUT_SEC: '30'
  SSH_SCAN_INTERVAL_SEC: '2'
  SSH_ENABLE_RETRIES: '2'
  WAIT_AFTER_SSH_ENABLE_SEC: '60'
  SSH_TIMEOUT_MIN: '120'
  CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
  CPE_INFO_TIMEOUT_SEC: '30'
  CPE_READY_RETRIES_BEFORE_RESET: '3'
  CPE_READY_RETRIES_AFTER_RESET: '6'
  CPE_READY_RETRY_SLEEP_SEC: '10'
  DO_PDU_RESET_ON_READY_FAIL: '1'
  PDU_SCRIPT: /home/da40/charter/tools/pdu_outlet1.py
  PDU_OUTLET_ID: '1'
  PDU_WAIT_SEC: '120'
  LAN_PING_BACKEND: plain
  LAN_PARENT_IFACE: ''
  LAN_MACVLAN_PING_COUNT: '20'
  LAN_MACVLAN_PING_TIMEOUT_SEC: '2'
  PBR_IFACE: ''
  PBR_SRC_IP: ''
  PBR_GW: 192.168.1.1
  PBR_SUBNET: 192.168.1.0/24
  PBR_TABLE_ID: '100'
  PBR_PRIO_FROM: '1000'
  PBR_PRIO_TO: '1001'
  PROBE_IFACE: ''
  PROBE_SRC_IP: ''
  LAN_PING_CPE_COUNT: '20'
  LAN_PING_CPE_DEADLINE_SEC: '20'
  CPE_WAN_GATEWAY: 172.14.1.1
  CPE_PING_GW_COUNT: '10'
  LOSS_TRIGGER_PCT: '10'
  CONSEC_FAIL_TRIGGER_N: '3'
  LOGPULL_ON_TRIGGER: '1'
  LOGPULL_LATEST_DIR: /tmp/logpull
  LOGPULL_PATTERN: '*.tar.gz'
  LOG_INCLUDE_TS: '0'
  CPE_DEV: /dev/ttyUSB0
  CUSTOMER_ID: 682d4e5179b80027cd6fb27e
  PING_IFACE: eno2
  TEST_PROFILE: lab
  NODE_I
```

## 範圍與不測項（Scope / Non-goals）
- 本 case **用於驗證效能與長時間穩定度**（多 cycles/長時間執行），觀察指標波動、失敗率與平台穩定性。
- 不涵蓋：跨環境交付差異的自動修正（交付請先套用 Environment Template）。

## 測試步驟（Step-by-step）
1) **確認環境已就緒**：CPE Internet/Cloud Connected（必要時等候/重試）。
2) **確認/調整 cycles（很重要）**：
   - stability 預設常是 `CYCLES=1`（單輪冒煙），正式長跑前請先調整成你要的 cycles/interval。
   - 建議用 **OpenClaw 測試助理** 進行『單次 / 批次』修改（避免手動改錯、多檔不一致）。
   - 同時確認是否會 reboot / power-cycle（如有）。
3) **Run**：用下方「操作（Run）」觸發。
4) **看結果**：
   - PASS：run status=passed，且 log 顯示每 cycle 的關鍵動作皆成功。
   - FAIL：先拉 `run_id` log（必要時再拉 log-archive），對照「常見失敗與排除」。

## 驗證點（Pass / Fail Criteria）
- PASS 必要條件：
  - run 最終狀態為 `passed`
  - 長跑期間未出現連續失敗（例如 speedtest/result poll timeout、reboot 後無法恢復連線）。
- FAIL 判定：
  - 任一必要條件不成立，或 STOP_ON_FAIL 觸發中止。

## 風險與回復（Risk / Recovery）
- 若包含 reboot / power-cycle：
  - 需有充分的等待與 ready-check（例如 `cpe_info --status` retry），避免把 boot 中狀態誤判為 fail。

## 參數速查（Key env quick reference）
- 長跑控制：`CYCLES`、`CYCLE_INTERVAL`、`STOP_ON_FAIL`
- 環境差異：`TOOLS_PATH`、`PROFILES_FILE`、`NOC_PROFILE`、`CUSTOMER_ID`、`LAN_IFACE/WIFI_IFACE/PING_IFACE`

## 操作（Run）


??? note "操作（Run）— 點開看指令"
    > 建議：用 API 觸發 run，比 UI 更好重試/可腳本化。

    ```bash
    export CHARTER_BASE="http://{{CONTROL_PC_IP}}:5173"
    SCRIPT_ID=5067

    # 觸發執行
    curl -sS -X POST "$CHARTER_BASE/api/scripts/$SCRIPT_ID/run" | python3 -m json.tool
    ```

    - 回應會包含 `run_id`，後續請用它取 log / archive。

## 取證（Artifacts / Evidence）


??? note "取證（Artifacts）— 點開看指令"
    ```bash
    RID=1234
    curl -sS "$CHARTER_BASE/api/runs/$RID/log" > run_${RID}_log.json

    # 若 fail-hook 有產生 cpe logs
    curl -sS "$CHARTER_BASE/api/runs/$RID/log-archives" | python3 -m json.tool
    curl -fsSL "$CHARTER_BASE/api/runs/$RID/log-archive" -o run_${RID}_cpe_log.tar.gz
    ```

## 清理（Cleanup）


??? note "清理（Cleanup）— 點開看指令"
    ```bash
    # 清理已完成的 runs + workdir（避免磁碟累積）
    curl -sS -X DELETE "$CHARTER_BASE/api/runs/purge?older_than_days=0" | python3 -m json.tool
    ```

## 常見失敗與排除
- `noc-context timeout`：NOC endpoint 超時 → 增加 retry/backoff、確認出口網路/DNS
- eventual consistency：API 200 但 CPE 狀態未同步 → 用 wait/poll 再 assert
