# A2844344_Continuously_executing_reboot

- Suite: **stability**
- Script ID（可能因 delete/import 變動）：`5062`
- 風險等級（對 DUT 影響）：**HIGH**

## 目的（Purpose）
- 長時間/多 cycle 執行 Reboot，驗證開機恢復、SSH ready、版本/partition guard 等檢查。


## 前置條件（Preconditions）
- CPE/Cloud 需可連線（Internet/Cloud Connected）
- 需要的工具：`/home/da40/charter/tools`（wifi/lan/ssh/pdu 等）

## 測試行為摘要（What it does）
- 觸發 Reboot（含 serial mute/lock 以避免 console 鎖死）

## 主要參數（manifest env 重要值）
- STOP_ON_FAIL: `0`
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
  # [1) 長跑流程控制（cycle wrapper）]
  # - CYCLES：總共跑幾輪
  # - CYCLE_INTERVAL：每輪之間等待秒數
  # - STOP_ON_FAIL：遇到 fail 是否立刻停止（1=停 / 0=不中斷）
  # - ORIGINAL_ENTRY：wrapper 內部實際呼叫的原始入口（通常不用改）
  # =========================
  CYCLES: '1'
  CYCLE_INTERVAL: '90'
  STOP_ON_FAIL: 0
  ORIGINAL_ENTRY: main_impl.py:run

  # =========================
  # [2) 本地工具與 Reboot mute 控制]
  # - TOOLS_PATH：工具目錄（cpe_info / cpe_ssh / noc_api_cli 等）
  # - REBOOT_MUTE_SECS：重啟後 console mute 秒數（避免啟動期亂輸入）
  # - REBOOT_MUTE_WITH_LOCK：是否使用 lock 機制（1=使用 / 0=不使用）
  # =========================
  TOOLS_PATH: /home/da40/charter/tools
  REBOOT_MUTE_SECS: 60
  REBOOT_MUTE_WITH_LOCK: 0

  # =========================
  # [3) SSH 基本資訊]
  # - SSH_USER/SSH_PASSWORD/SSH_HOST_LAN：LAN 端 SSH 登入資訊
  # - ENABLE_SSH_PRE_SCAN：是否在流程前先掃描確認 SSH ready
  # - SSH_TIMEOUT_MIN：整體 SSH 流程上限（分鐘）
  # =========================
  SSH_PASSWORD: '<fill>'

  # =========================
  # [4) NOC / Cloud 參數]
  # - NOC_BASE/NOC_EMAIL/NOC_PASSWORD：NOC API 登入用（若已在其他地方注入可保留原值）
  # - CUSTOMER_ID：要測的 customer/account id
  # - NOC_PROFILE/PROFILES_FILE：profiles 設定檔（此腳本可能仍會直接用 NOC_BASE 等值）
  # - BEARER/INSECURE/LOCATION_ID：HTTP header / TLS / 位置相關（依客戶需求）
  # =========================
  NOC_BASE: https://piranha-int.tau.dev-charter.net
  NOC_PROFILE: SPECTRUM_INT
  PROFILES_FILE: /home/da40/charter/.secrets/noc_profiles.json
  CUSTOMER_ID: '682d4e5179b80027cd6fb27e'
  BEARER: 0
  INSECURE: 0
  LOCATION_ID: ''

  # =========================
  # [5) Metrics / CPE Console 連線]
  # - METRICS_TOOL：收集 CPE 指標工具
  # - CPE_DEV/CPE_BAUD：Cons
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
    SCRIPT_ID=5062

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
