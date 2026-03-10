# C24541454_Multiple_reboot_stress

- Suite: **stability**
- Script ID（可能因 delete/import 變動）：`5065`
- 風險等級（對 DUT 影響）：**HIGH**

## 目的（Purpose）
- Reboot 壓力測試：連續多次 reboot（短間隔），觀察設備是否能穩定回到可用狀態。


## 前置條件（Preconditions）
- CPE/Cloud 需可連線（Internet/Cloud Connected）
- 需要的工具：`/home/da40/charter/tools`（wifi/lan/ssh/pdu 等）

## 測試行為摘要（What it does）
- 觸發 Reboot（含 serial mute/lock 以避免 console 鎖死）

## 主要參數（manifest env 重要值）
- STOP_ON_FAIL: `1`
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
  CYCLE_INTERVAL: 30
  STOP_ON_FAIL: 1
  ORIGINAL_ENTRY: main_impl_orig.py:run
  TOOLS_PATH: /home/da40/charter/tools
  NODE_ID_MAX_RETRIES: 30
  NODE_ID_RETRY_INTERVAL_SEC: 2
  CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
  CPE_BAUD: 115200
  CPE_USER: root
  CPE_PASSWORD: null
  NOC_BASE: https://piranha-int.tau.dev-charter.net
  SSH_USER: operator
  SSH_PASSWORD: <fill>
  SSH_TIMEOUT_MIN: 120
  SSH_REENABLE_EACH_CYCLE: 0
  SSH_HOST_LAN: 192.168.1.1
  WAN_SSH_REQUIRED: 0
  LAN_SSH_REQUIRED: 1
  CPE_SSH_TOOL: /home/da40/charter/tools/cpe_ssh.py
  SSH_TOOL_TIMEOUT: 15
  USE_CLOUD_SSH: '1'
  CPE_LOG_TIMEOUT_SEC: '240'
  NOC_PROFILE: SPECTRUM_INT
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
  CUSTOMER_ID: '682d4e5179b80027cd6fb27e'
  SSH_ACTION: enable
  ENABLE_SSH_FLOW: 0
  ENABLE_REBOOT_TEST: 1
  REBOOT_DELAY_SEC: 2
  REBOOT_MUTE_SECS: 60
  REBOOT_MUTE_WITH_LOCK: 1
  POST_REBOOT_STATUS_WAIT_SEC: 120
  CPE_STATUS_MAX_RETRIES: 3
  CPE_STATUS_RETRY_INTERVAL_SEC: 30
  ENABLE_CPE_STATUS_CHECK: 1
  ENABLE_DNS_CHECK: 0
  TARGET: www.google.com
  SECOND: cloudflare.com
  EXPECT_A_MIN: 1
  EXPECT_AAAA_MIN: 1
  RETRIES: 3
  INTERVAL_SEC: 3
  DNS_SSH_TIMEOUT_SEC: 30
  PRECONDITION_FIRST_CYCLE: 1
  AUTO_SSH_ENABLE: 1
  REQUIRE_SSH_READY: 1
  SSH_ENABLE_RETRIES: 2
  SSH_SCAN_TIMEOUT_SEC: 60
  SSH_SCAN_INTERVAL_SEC: 2
  WAIT_AFTER_SSH_ENABLE_SEC: 60
  CPE_READY_MAX_RETRIES: 10
  CPE_READY_RETRY_INTERVAL_SEC: 3
  CPE_READY_CMD_TIMEOUT_SEC: 30
  PDU_SCRIPT: /home/da40/charter/tools/pdu_outlet1.py
  PDU_OUTLET_ID: 1
  PDU_RESET_ACTION: reset
  PDU_RE
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
    SCRIPT_ID=5065

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
