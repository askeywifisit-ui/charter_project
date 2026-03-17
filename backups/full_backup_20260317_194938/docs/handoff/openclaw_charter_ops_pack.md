# OpenClaw Charter Ops Pack（讓客戶少問、直接會做事）

本頁目的：讓「OpenClaw 測試助理新裝 OpenClaw」後，也能用接近 Alice/Lina 的工作方式操作 Charter 平台：**有固定工具、有固定預設、有固定回報格式、有明確授權邊界**，避免每一步都來問。

---

## 1) 準備一個「Charter Ops Pack」（最重要）
把一個小資料夾放進 OpenClaw 測試助理的 workspace：
- `~/.openclaw/workspace/charter_ops/`

建議內容（最小可用）：
1) `charter_ops_runbook.md`
   - 一頁 SOP：list/plan/run/stop/purge/抓 log
2) `charter_defaults.env`（或 `.env` 範本）
   - 只要填：`CHARTER_BASE`、`NOC_PROFILE`、`CUSTOMER_ID`、`LAN_PARENT_IFACE`、`WIFI_IFACE`…
3) `snapshot_dashboard.py` / `report_cpe_status.py`
   - 固定回報格式（狀態、摘要、證據檔）

> 目標：把「會做事」從腦袋變成工具與 SOP；測試助理照做就不會一直問。

---

## 2) 寫入預設值（讓她不用每次確認）
第一次 setup 就固定記下（平台預設）：
- `CHARTER_BASE=http://{{CONTROL_PC_IP}}:5173`
- `NOC_PROFILE={{NOC_PROFILE}}`
- `CUSTOMER_ID={{CUSTOMER_ID}}`

建議放置：
- shell profile（例如 `~/.zshrc`）或 `charter_defaults.env`
- 並在文件（Hand-off → 交付環境表）保留「對方填寫版本」

### 2.1) DUT 參數切換 SOP（推薦：`dut.env`，換 CPE 不用改 systemd）
目的：把「會跟著 DUT 改變」的值集中管理（例如 `CUSTOMER_ID`/`NOC_PROFILE`/`SSH_HOST_LAN`），換 CPE 時只改一個檔。

**平台側設定（control PC 上）**：
1) 建立檔案（權限建議 600）：
   - `/home/da40/charter/.secrets/dut.env`
2) 在 `charter-worker.service` 的 `[Service]` 加一行：
   - `EnvironmentFile=-/home/da40/charter/.secrets/dut.env`
   - 前面的 `-` 代表檔案不存在時不會讓 service fail（較好移植）。
3) 套用：
   - `systemctl daemon-reload && systemctl restart charter-worker`

**換 DUT（每次換 CPE 都做）**：
1) 編輯 `dut.env`：
   - 例如：
     - `CUSTOMER_ID=682d4e5179b80027cd6fb27e`
     - `NOC_PROFILE=LAB_INT`
     - `SSH_HOST_LAN=192.168.1.1`
2) 重啟 worker：
   - `systemctl restart charter-worker`
3) 立刻驗證：先跑 `C00000004_NOC_API_basic_test` 或任一依賴 NOC 的 sanity。

> 注意：如果你們短期決定「CUSTOMER_ID 先維持在各 script 的 manifest.yaml」，那就只在 `dut.env` 放 `NOC_PROFILE/SSH_HOST_LAN` 等；等要集中管理再把 `CUSTOMER_ID` 移過來即可。

---

## 3) 交付「預設決策」（沒特別說就照這套）
建議寫進 runbook，作為助理的預設行為：
- 先跑 smoke（例如 limit=3）再擴大
- stability 先 24h，OK 再 72h
- 若需排除 IPv6：case name 含 `ipv6` 一律排除（大小寫不拘）
- API 優先（import/run/purge/log/download）

---

## 4) 交付「授權邊界」（什麼情況才需要問你）
測試助理會一直問，多半是因為怕做錯。

建議明確寫死：只有以下情況才需要請示：
1) 會刪資料：purge、刪 scripts、刪 runs/workdir
2) 會改部署/平台設定：改 web/api、改 tools、改 worker
3) 會影響正在跑的 run：queued/running 狀態下的 stop/重啟

其餘情況：
- 先產出 plan → 一次給你確認 → 你回 OK 就直接跑 → 回報 summary

---

## 5) 固定回報格式（你就不會被碎問）
要求測試助理每次只貼這三段：
1) plan 摘要（planned scripts 數量 + 前 10 條）
2) run_ids
3) Summary（PASS/FAIL/running）+ fail log tail（工具自動抓）

---

## 6) 相關文件連結
- Hand-off → 交付環境表
- Hand-off → NOC Profile / Secrets
- Runbook → Dashboard 一鍵抓取（API Snapshot）
- User Guide → Modify Script Code（改 code）
