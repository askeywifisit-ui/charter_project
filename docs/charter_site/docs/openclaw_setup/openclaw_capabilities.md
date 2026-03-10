# OpenClaw 可以協助的工作項目（Charter 平台）

本頁整理 OpenClaw（測試 AI 助理）在 Charter 平台可協助的任務範圍，供外部單位了解「哪些工作可委託助理處理」。

> 原則：
> - 破壞性操作（刪除 scripts/runs、覆寫 zip）前，會先做備份並請你確認。
> - Secrets（token/API key）不寫入文件 repo；以安全方式存放。

---

## 交付產出（Deliverables）

外部單位把任務交給 OpenClaw 後，通常可取得以下產出（依任務類型擇一或多項）：

- **Run 結果摘要**：pass/fail、run_id 清單、失敗 top 類型
- **Root cause 報告**：fail point、推定根因類別、修正建議、驗證計畫
- **修正與驗證紀錄**：變更點（檔案/備份）、重跑驗證 run_id（含前後對照）
- **批次處置結果**：import/export/manifest 套用的清單與結果（ok/fail）

## 範圍與保護條款（Scope & Guardrails）

- **破壞性操作需明確授權**：例如刪除 scripts/runs、覆寫 zip、purge/stop/clear queue。
- **Secrets 不入 repo**：token/API key 僅能放環境變數或私密檔（權限 `600`），且不在文件/log 中外流。
- **先最小重現再擴大**：優先用最小測項驗證環境，再進行 batch 或 longrun。

---

## A) Scripts 管理（Import / Export / Modify）
### 1) Import scripts
- `POST /api/scripts/import2`
- 依規範：同名（suite+name）先刪再匯入，避免 DUPLICATE

### 2) Export scripts
- `GET /api/scripts/{script_id}/export`

### 3) Modify manifest（批次）
- `PUT /api/scripts/{script_id}/manifest`
- 可依 Hand-off 的環境表（CPE_HOST/WIFI_IFACE/LAN_PARENT_IFACE…）批次套用到多支腳本

### 4) Modify code（修改 zip 內程式碼）
- 流程：export → 解壓修改 → 重新打包 → 刪同名 → import2 → run 驗證
- 詳見：`User Guide → Modify Script Code（改 code）`

---

## B) 執行與驗證（Run / Stop / 取證）
- Run：`POST /api/scripts/{script_id}/run`
- Stop：`POST /api/runs/{rid}/stop`
- 拉 log：`GET /api/runs/{rid}/log`
- 下載 fail archive：`GET /api/runs/{rid}/log-archives` / `log-archive`

---

## C) 排程 / 批次 / 隨機抽測
> 依你們的使用情境：可以用 Charter stability 的 cycles，也可以用 OpenClaw 的 cron/heartbeat 做定時觸發。

OpenClaw 支援：
- 依 suite 建立批次執行清單（sanity nightly / stability longrun）
- 隨機抽測（從 sanity 清單抽 N 支，或依標籤抽）
- 產出每日報表（pass/fail、失敗 top 類型）

---

## D) Test log 分析（Root cause / 趨勢）

OpenClaw 可對每次 run 的輸出（run log / archive / diag snapshot）進行結構化解析，並提供可落地的修正建議與驗證計畫：

- **失敗定位（Failure localization）**：標定 fail step / event、抽取關鍵錯誤片段與上下文
- **根因歸類（Root cause taxonomy）**：依常見類別（環境/TLS、Wi‑Fi route、DHCP eventual consistency、資源衝突、SSH 時序、CPE boot/cloud ready…）分類，避免只停留在「錯誤訊息」層級
- **修正建議（Actionable remediation）**：提供腳本面（retry/backoff/timeout/guard/diag）、平台面（systemd env/工具修正）、環境面（網路/DNS/CA/路由）三層修正路徑
- **穩定度量化（Flakiness quantification）**：以 N 次重跑統計 fail step 分布與發生率，辨識偶發與系統性問題
- **驗證計畫（Verification plan）**：定義重跑策略、驗收指標與回歸範圍，確保修正可被客觀驗證

### Root cause 分析輸出格式（建議）

每次針對 FAIL run 做分析時，建議固定輸出以下欄位（方便累積與比對）：

- **run_id / script / suite / 時間**
- **Fail point（哪一步）**：對應 log event / step name
- **直接錯誤訊息（原文）**：保留 1–3 行關鍵片段
- **推定 root cause 類別**（見下表）
- **建議修正**：腳本面 / 平台面 / 環境面（擇一或多項）
- **驗證方式**：要怎麼 rerun、看哪個 log 指標算改善

### 常見 root cause 類別（Charter 腳本實務）

| 類別 | 常見特徵（log/現象） | 建議修正（優先順序） | 建議測試/驗證 |
|---|---|---|---|
| **環境連通/TLS** | `fetch failed`、`UNABLE_TO_GET_ISSUER_CERT_LOCALLY`、對外 API 失敗 | 補 CA / 設 `NODE_EXTRA_CA_CERTS`、檢查 proxy/inspection | 先用 `curl -I` 驗證，再 rerun 一支最小 case |
| **Wi‑Fi 路由/介面** | 可連 SSID 但 ping internet 失敗；或 `wlan0 not present` | systemd 設 `WIFI_IFACE`；工具補 default route；避免 manifest 寫死 | rerun WiFi basic + 目標 case；log 檢查 `wifi_ipv4`/route |
| **DHCP reservation eventual consistency** | NOC set 200，但 CPE DHCP dump 看不到 reserved | 增加 wait/poll；改用 NOC list 驗證；加 diag dump | rerun 並觀察 reserved 出現時間；跑 3 次看 flakiness |
| **資源衝突/占用** | NOC 回 422（IP used by XXX）或 lease 已被佔用 | auto-pick free IP；先清 conflict；避免固定 IP | rerun 5 次確定不再撞 IP |
| **SSH ready 時序** | port scan 一直 false、登入 intermittent | 延長 scan timeout；ssh_enable 後 wait/poll；必要時 reboot + mute | rerun 並看 `ssh_port ok` 達成時間分布 |
| **CPE boot / cloud ready** | cloud `Determining...`、Not Connected | 增加 retry/backoff；PDU reset 時序；serial mute | rerun 觀察 cloud ready 需要秒數 |
| **腳本/manifest 覆蓋平台參數** | 同一套腳本換環境就 fail；iface/dev 被寫死 | manifest 只放 defaults；platform 用 systemd env | 移植驗證：換機器只改 systemd/dut.env |

### 測試建議（把分析變成可執行）

- **最小重現**：先挑 1 支最小測項（例如 WiFi basic / SSH basic）確認環境，再跑出問題的 case。
- **三段式重跑**：
  1) **立即 rerun**（判斷偶發/資源競爭）
  2) **清理/重置後 rerun**（purge finished、清 reservation、wifi disconnect、必要時 PDU）
  3) **延時 rerun**（等待 NOC/Cloud eventual consistency）
- **Flakiness 量化**：同一 case 跑 N=5（或 10），統計 fail step 分布，才知道該加 timeout 還是修邏輯。

---

## E) 依 Test Plan / Step 撰寫新腳本

OpenClaw 支援把「Test Plan（步驟/預期）」轉成可在 Charter 平台執行的腳本（zip），並確保可維護、可驗證、可移植。

### 你需要提供（Inputs）

- Test Plan（或測試步驟）：Step-by-step + Expected Result
- 測項前提（Preconditions）：網段/拓撲、DUT 狀態、是否需要 PDU、是否需要 Wi‑Fi client
- 參數/變因：例如 SSID band、等待時間、重試次數、是否允許 flakiness

### OpenClaw 會交付（Outputs）

- **Script zip**：`manifest.yaml` + `entrypoint` + 核心測試程式碼
- **README（同一頁文件）**：目的、必要 env、成功/失敗判定、常見失敗與排查
- **驗證紀錄**：對應 run_id（至少 1 次 PASS；如需穩定性則 N 次統計）

### 交付品質與治理規範（Quality / Governance）

- **API 優先**：可用 API 完成的控制/查詢，不用 Selenium
- **同名先刪再匯入**：避免 `skipped:DUPLICATE`
- **改動前先備份**：export zip + 記錄 sha/備份檔名
- **移植友善**：平台參數以 systemd env 為準；`manifest.yaml` 僅提供 defaults，不可寫死 `WIFI_IFACE / CPE_DEV / PDU_* / PING_IFACE / TEST_PROFILE` 等平台值
- **可觀測性**：每個關鍵 step 以 JSON log/event 記錄，便於 root cause 分析

### 建議的驗證流程（Verification）

1) **最小環境驗證**：先跑 1 支基礎測項確認環境（例如 SSH basic / WiFi basic）
2) **功能驗證**：新腳本跑 1 cycle（確認 PASS/FAIL 判定正確）
3) **穩定性驗證（選配）**：N=5 或 10 次重跑，確認 fail step 分布與 flakiness

---

## F) 產生新的 tools 工具模組程式（/home/da40/charter/tools）
OpenClaw 支援：
- 產生新的 `verify_*.py` / `diag_*.py` / `control_*.py` / `batch_*.py`
- 具備以下工程化要求：
  - `--help`（argparse）與清楚 usage
  - `--json` 輸出（方便 scripts assert）
  - timeout/retry 與 exit code 定義
  - 預設不輸出 secrets（token/password）
- 同步補齊文件站說明頁（Tools 章節），包含用途、參數、範例、常見錯誤

---

## 建議的交付方式
- 交付外部單位時：先給他們文件站 + Hand-off 表格
- 然後由 OpenClaw 協助批次套用環境參數、跑 Quick Validation
