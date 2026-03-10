# C6376350_WiFi_radio_enable_disable-xtime

- Suite: **stability**
- Script ID（可能因 delete/import 變動）：`5069`
- 風險等級（對 DUT 影響）：**MEDIUM**

## 目的（Purpose）
- Wi‑Fi radio enable/disable 重複 X 次測試（xtime 版本），用於快速壓力/回歸。


## 前置條件（Preconditions）
- CPE/Cloud 需可連線（Internet/Cloud Connected）
- 需要的工具：`/home/da40/charter/tools`（wifi/lan/ssh/pdu 等）

## 測試行為摘要（What it does）
- Wi‑Fi radio enable/disable 切換（NOC API/SSH）
- （選配）保持一段時間 WIFI_TOGGLE_HOLD_SEC
- （選配）CPE/Wi‑Fi 狀態確認
- （選配）其它健康檢查

- 包含 NOC speedtest（ENABLE_SPEEDTEST=1 或腳本含 speedtest flow）
- 包含 Wi‑Fi radio enable/disable（ENABLE_WIFI_TEST=1）

## 主要參數（manifest env 重要值）
- STOP_ON_FAIL: `'1'`
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
  # - STOP_ON_FAIL：遇到 fail 是否立刻停（1=停 / 0=不停，跑完再彙整）
  # - ORIGINAL_ENTRY：wrapper 內部實際呼叫的原始腳本入口
  # =========================
  CYCLES: '1'
  CYCLE_INTERVAL: '90'
  STOP_ON_FAIL: '1'
  ORIGINAL_ENTRY: main_impl_orig.py:run


  # =========================
  # [Tools / Node ID 取得]
  # - TOOLS_PATH：工具目錄（noc_api_cli / cpe_info / cpe_ssh 等）
  # - METRICS_TOOL：用 serial 讀取 node_id 的工具
  # - NODE_ID_MAX_RETRIES / NODE_ID_RETRY_INTERVAL_SEC：node_id 取得重試/間隔
  # =========================
  TOOLS_PATH: /home/da40/charter/tools
  NODE_ID_MAX_RETRIES: '20'
  NODE_ID_RETRY_INTERVAL_SEC: '3'
  CPE_INFO_TOOL: /home/da40/charter/tools/cpe_info


  # =========================
  # [CPE Console / Serial 參數]
  # - CPE_DEV/CPE_BAUD：Console/Serial 裝置與 baudrate
  # - CPE_USER/CPE_PASSWORD：登入帳密
  #   - 若 CPE_PASSWORD 為 null/空：腳本會用 cpe_info 走 fallback 取密碼
  # =========================
  CPE_BAUD: '115200'
  CPE_USER: root
  CPE_PASSWORD: null


  # =========================
  # [NOC / Cloud API 參數]
  # - CUSTOMER_ID：要測的 customer/account id
  # - NOC_PROFILE + PROFILES_FILE：從 profiles JSON 載入 base/email/password
  #   - 這樣 manifest 不需要硬編碼 NOC_EMAIL/NOC_PASSWORD
  # - NOC_BASE/NOC_EMAIL/NOC_PASSWORD：若有明確設定，仍可覆蓋 profile（可選）
  # - ENABLE_NOC_API_TESTS：是否跑 NOC API 測試
  # =========================
  NOC_PROFILE: SPECTRUM_INT
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
  CUSTOMER_ID: '682d4e5179b80027cd6fb27e'
  NOC_BASE: ''
  ENABLE_NOC_API_TESTS: '1'
  BEARER: '0'
  INSECURE: '0'


  # =
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
    SCRIPT_ID=5069

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
