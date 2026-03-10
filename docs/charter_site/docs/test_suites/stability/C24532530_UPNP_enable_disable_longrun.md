# C24532530_UPNP_enable_disable_longrun

- Suite: **stability**
- Script ID（可能因 delete/import 變動）：`5064`
- 風險等級（對 DUT 影響）：**MEDIUM**

## 目的（Purpose）
- 長時間/多 cycle 切換 UPnP enable/disable，並做健康檢查（必要時 reboot wait）。
- 可搭配 speedtest 做基本連線驗證。


## 前置條件（Preconditions）
- CPE/Cloud 需可連線（Internet/Cloud Connected）
- 需要的工具：`/home/da40/charter/tools`（wifi/lan/ssh/pdu 等）

## 測試行為摘要（What it does）
- UPnP enable/disable 切換
- apply wait
- （可能）reboot + boot wait
- UPnP health check
- （選配）speedtest 作為連線健康檢查

- 包含 NOC speedtest（ENABLE_SPEEDTEST=1 或腳本含 speedtest flow）
- 包含 UPnP enable/disable + health check（ENABLE_UPNP_HEALTH=1）

## 主要參數（manifest env 重要值）
- STOP_ON_FAIL: `1`
- CYCLES: `1`
- INTERVAL: `90`

### 需依環境替換（給外部單位）
請參考 **Environment Template**，常見需替換：
- `TOOLS_PATH` / `PROFILES_FILE` / `NOC_PROFILE` / `CUSTOMER_ID`
- `CPE_HOST` / `LAN_PARENT_IFACE` / `WIFI_IFACE` / `PING_IFACE`

## manifest.yaml（節錄）
```yaml
env:
  # =========================
  # [Wrapper / 長跑流程控制]
  # - CYCLES：總共要跑幾輪
  # - CYCLE_INTERVAL：每輪之間等待秒數
  # - STOP_ON_FAIL：遇到 fail 是否立刻停止（1=停 / 0=不停，跑完再彙整）
  # - ORIGINAL_ENTRY：wrapper 內部呼叫的原始入口（通常不用改）
  # =========================

  CYCLES: '1'
  CYCLE_INTERVAL: '90'
  STOP_ON_FAIL: 1
  ORIGINAL_ENTRY: main_impl_orig.py:run_upnp

  # Precondition 只在 cycle#1 跑一次
  PRECONDITION_FIRST_CYCLE: 1

  # 每 cycle 開始前要求 SSH ready
  REQUIRE_SSH_READY: 1
  AUTO_SSH_ENABLE: 1
  SSH_ENABLE_RETRIES: 2
  WAIT_AFTER_SSH_ENABLE_SEC: 10

  # CPE cloud ready check（cpe_info --cloud）
  CPE_READY_MAX_RETRIES: 5
  CPE_READY_RETRY_INTERVAL_SEC: 3
  CPE_READY_CMD_TIMEOUT_SEC: 20

  # PDU reset（用 PDU_SCRIPT + PDU_OUTLET_ID）
  PDU_RESET_ACTION: reset
  PDU_RESET_WAIT_SEC: 120
  PDU_RESET_TIMEOUT_SEC: 600

  # SSH port scan timeout
  SSH_SCAN_TIMEOUT_SEC: 2

  # Wrapper 專用：cycle 開始前快速 scan port 22（fail 就走 NOC ssh-enable）
  SSH_SCAN_MAX_RETRIES: 1
  SSH_SCAN_INTERVAL_SEC: 1
  # =========================
  # [工具路徑 / Metrics / 基本查詢]
  # - TOOLS_PATH：tools 目錄位置
  # - METRICS_TOOL：收集 CPE 指標/狀態用工具
  # - CPE_INFO_TOOL：查 CPE 資訊（版本/介面/狀態…）
  # - CPE_SSH_TOOL：對 CPE 執行 SSH 動作的工具封裝
  # =========================

  TOOLS_PATH: /home/da40/charter/tools
  METRICS_TOOL: /home/da40/charter/tools/cpe_metrics_agent_serial.py
  # =========================
  # [Node ID / 取得裝置識別等待]
  # - NODE_ID_MAX_RETRIES：找不到 node_id 時最多重試次數
  # - NODE_ID_RETRY_INTERVAL_SEC：每次重試間隔秒數
  # =========================

  NODE_ID_MAX_RETRIES: 30
  NODE_ID_RETRY_INTERVAL_SEC: 2
  CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info
  CPE_SSH_TOOL: /h
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
    SCRIPT_ID=5064

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
