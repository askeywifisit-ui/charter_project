# Charter 測試平台安裝 / 移植（systemd 版）

本頁目的：把目前 11 LAB（controlpc）上已驗證的 **systemd 服務化部署**，整理成可以移植到其他單位/客戶環境的步驟。

> 你可以把它當成「平台交付」SOP：安裝 → 設定 → 啟動 → 驗證 → 備份/升級/回滾。

---

## 0) 範圍與前提

- **建議 OS：Ubuntu 22.04 LTS（jammy）**
  - 已驗證：controlpc 現行為 Ubuntu **22.04.5 LTS**（jammy）。
  - 移植給客戶/其他單位時，建議同樣使用 Ubuntu 22.04 LTS 以降低差異。

- **標準交付帳號：`da40`（需具備 sudo）**
  - 目錄/習慣以 `/home/da40/charter` 為單一來源。
  - systemd 允許 root/da40 混用（與現行 controlpc 一致）。
  - CSIT 透過 VPN + OpenClaw 遠端自動化時，以 `da40` + sudo 最順。

- 本文件描述的是 **platform/control PC** 的部署（web/api/worker + metrics/probe/watchdog）。
- 不涵蓋：DUT/CPE 的硬體接線與 Wi‑Fi/Radio 測試細節（請見 Environment Template / Test Suites）。

---

## 1) 平台元件與埠口

| 元件 | systemd unit | 作用 | 預設埠 |
|---|---|---:|---:|
| API | `charter-api.service` | FastAPI + Uvicorn（提供 `/api/...`） | `8080` |
| Worker | `charter-worker.service` | 取 run 任務、解壓 zip、pip install、執行腳本、產出 log/archive | - |
| Web | `charter-web.service` | Vite web（UI；同源呼叫 API） | `5173` |
| CPE metrics agent | `cpe-metrics-agent.service` | 從 serial/ssh 採集 CPE metrics，送到 API | - |
| CPE status probe | `cpe-status-probe.timer` + `cpe-status-probe.service` | 定期 probe CPE 狀態並寫 DB | - |
| PBR watchdog | `pbr-watchdog.service` | 監控/重設 Policy Based Routing（確保測試路由不飄） | - |

> UI 通常以 `http://<CONTROL_PC_IP>:5173` 提供；UI 內同源呼叫 `/api/...`。

---

## 2) 目錄結構（control PC 上）

以 11 LAB 現行為準：

- 平台根目錄：`/home/da40/charter/`
- Web：`/home/da40/charter/apps/web`
- API/Worker：`/home/da40/charter/apps/api`
- Tools：`/home/da40/charter/tools`
- 祕密檔（NOC profiles 等）：`/home/da40/charter/.secrets/`
- 資料目錄（runs/work/scripts/venv）：`/home/da40/charter/data/`

---

## 3) systemd unit（需要一起移植）

### 3.1 unit 清單

請從來源機器（controlpc）帶走以下檔案：

- `/etc/systemd/system/charter-api.service`
- `/etc/systemd/system/charter-worker.service`
- `/etc/systemd/system/charter-web.service`
- `/etc/systemd/system/cpe-metrics-agent.service`
- `/etc/systemd/system/cpe-status-probe.service`
- `/etc/systemd/system/cpe-status-probe.timer`
- `/etc/systemd/system/pbr-watchdog.service`

以及（如有）drop-in 設定：
- `/etc/systemd/system/charter-api.service.d/*.conf`（例如 DB 連線）

### 3.2 重要設定點（移植時必檢）

- API 執行：
  - `ExecStart=... python -m uvicorn app.main:app --host 0.0.0.0 --port 8080`
- Web 執行：
  - `ExecStart=... /home/da40/charter/apps/web/run_web.sh`（通常跑 Vite dev）
- Worker 執行：
  - `ExecStart=... /home/da40/charter/apps/api/worker.py`
- DB 連線（非常重要）：
  - `DATABASE_URL`、`PSQL_URL`
- metrics agent 的環境檔：
  - `EnvironmentFile=-/etc/default/cpe-metrics-agent`
- status probe 的 DB：
  - `Environment=DATABASE_URL=postgresql://...`

---

## 4) OS 依賴與安裝（Ubuntu 22.04 參考）

> 依你的 11_26 備忘錄補齊：Node/pnpm、dialout 群組等。

### 4.1 系統套件

```bash
sudo apt update
sudo apt install -y \
  python3 python3-venv python3-pip \
  postgresql postgresql-contrib \
  git unzip curl

# 啟動 Postgres
sudo systemctl enable --now postgresql
sudo systemctl status postgresql --no-pager
```

### 4.1.1 建立 DB（rg）與帳密（rg/rg）

> 目標：與 controlpc 目前 unit 設定一致（`DATABASE_URL=...rg:rg@localhost:5432/rg`）。

```bash
sudo -iu postgres
psql -c "CREATE USER rg WITH PASSWORD 'rg';" || true
psql -c "CREATE DATABASE rg OWNER rg;" || true
psql -c "GRANT ALL PRIVILEGES ON DATABASE rg TO rg;" || true
exit

# 驗證可登入
psql -h 127.0.0.1 -U rg -d rg -c '\\conninfo'
```

### 4.2 Node.js + pnpm（Web 用）

> web 服務（`charter-web.service`）會啟動 `run_web.sh`（npm/pnpm）。建議固定 Node 20.x。

```bash
# NodeSource (Node 20)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# pnpm
sudo npm install -g pnpm

node -v
npm -v
pnpm -v
```

### 4.3 權限（serial / dialout）

若測試/metrics 需要存取 serial device（例如 `/dev/ttyUSB0` 或 `/dev/serial/by-id/...`），建議把 `da40` 加入 `dialout`：

```bash
sudo usermod -aG dialout da40
# 登出再登入後生效
```

## 5) DB：兩種移植策略（A 乾淨 / B 複製）

你可以選擇：

- **A) 新環境乾淨建 DB（推薦交付）**：只要能跑平台，不保留舊 runs/history。
- **B) 複製/還原舊 DB（保留資料）**：把 172.14.1.140 的 `rg` DB dump 還原到新環境。

### 5.1 A) 新環境乾淨建 DB（rg）

此平台依賴 Postgres（unit 內使用 `DATABASE_URL=postgresql...`）。

移植時請確認：
- 目標機器已安裝/啟動 Postgres（見上方 4.1）
- 已建立 DB 與帳密（`rg/rg`；見上方 4.1.1）

> 交付/移植建議（A）：新環境乾淨建 DB 即可，不需要複製 172.14.1.140 的舊資料庫。
  若客戶需要保留 runs/history，才另外提供 DB dump（可選項）。

### 5.2 B) 複製/還原舊 DB（保留 runs/history）

> 已在 controlpc（172.14.1.140）確認：Postgres 目前 listen 在 `127.0.0.1:5432`，units 也都是連本機 DB。

#### 5.2.1 在舊機器（controlpc）匯出 DB

建議用 custom format（`-Fc`），還原時較彈性：

```bash
sudo -iu postgres
pg_dump -Fc rg > /home/da40/rg.dump
exit

ls -lh /home/da40/rg.dump
```

把 `rg.dump` 用 `scp` 搬到新機器（路徑自訂）。

#### 5.2.2 在新機器匯入 DB

```bash
# 先確保新機器已安裝並啟動 Postgres
sudo systemctl enable --now postgresql

# 建立 role/db（若尚未建立）
sudo -iu postgres
psql -c "CREATE USER rg WITH PASSWORD 'rg';" || true
psql -c "CREATE DATABASE rg OWNER rg;" || true

# 還原
pg_restore -d rg /home/da40/rg.dump
exit

# 驗證
auth="rg"
psql -h 127.0.0.1 -U "$auth" -d rg -c '\\dt'
```

#### 5.2.3 注意事項

- 若新舊機器 Postgres major version 差太多，建議改用 plain SQL dump（`pg_dump rg > rg.sql`）再 `psql < rg.sql`。
- 若你要交付給外部單位，DB dump 可能包含 runs/log meta 等資料，請評估敏感性。

## 6) 設定檔（移植時要改的地方）

### 5.1 DB（Postgres）

此平台依賴 Postgres（unit 內使用 `DATABASE_URL=postgresql...`）。

移植時請確認：
- 目標機器已安裝/啟動 Postgres（見上方 4.1）
- 已建立 DB 與帳密（`rg/rg`；見上方 4.1.1）

> 交付/移植建議（你選的 A）：**新環境乾淨建 DB** 即可，不需要複製 172.14.1.140 的舊資料庫。
  若客戶需要保留 runs/history，才另外提供 DB dump（可選項）。

### 4.2 cpe-metrics-agent（/etc/default/cpe-metrics-agent）

此檔會因環境差異而變動（serial device、iface、帳密、interval）：

- `/etc/default/cpe-metrics-agent`
  - `CPE_AGENT_API=http://127.0.0.1:8080`
  - `CPE_SERIAL=...`（或 `/dev/ttyUSB0`）
  - `CPE_BAUD/CPE_USER/CPE_PASSWORD`
  - `CPE_IFACE`（例如 `eth0`）
  - `INTERVAL`（秒）
  - `WITH_WIFI/WITH_RADIO`

### 4.3 NOC profiles / secrets

- `PROFILES_FILE` 通常指向：`/home/da40/charter/.secrets/noc_profiles.json`
- 移植給外部單位時：建議由對方自行填入其 NOC profile / customer id。

---

## 5) 啟動/重啟（來源機器現行腳本）

來源機器提供一鍵重啟腳本（可一併移植）：

- `/home/da40/charter/restart.all.charter.sh`

其重啟順序（建議維持）：
1) stop：web → probe.timer → metrics → worker → api → watchdog
2) `systemctl daemon-reload`
3) start：api → worker → metrics → probe.timer → web → watchdog
4) `systemctl status ...`
5) `./log.color.charter.sh`

---

## 6) 健康檢查（移植後必跑）

### 6.1 API

```bash
curl -sS http://127.0.0.1:8080/health || true
curl -sS http://127.0.0.1:5173/api/health
```

> 若 UI 與 API 同源：以 `http://<CONTROL_PC_IP>:5173/api/health` 為準。

### 6.2 Worker

```bash
curl -sS http://127.0.0.1:5173/api/runs/worker/status | python3 -m json.tool
systemctl status charter-worker.service --no-pager
```

---

## 7) 移植/交付打包建議（最常用）

建議以「可重建」為目標打包：

1) 程式碼/工具
- `/home/da40/charter/apps/web`
- `/home/da40/charter/apps/api`
- `/home/da40/charter/tools`

2) systemd 設定
- `/etc/systemd/system/*.service`
- `/etc/systemd/system/*.timer`
- `/etc/systemd/system/charter-api.service.d/*.conf`
- `/etc/default/cpe-metrics-agent`

3) secrets
- **交付給外部單位時：不要直接交付明文**（改成 template + 交付表）
- 建議把 DUT 變動值集中到：`/home/da40/charter/.secrets/dut.env`
  - 檔案權限建議：目錄 `700`、`dut.env` `600`
  - systemd：`EnvironmentFile=-/home/da40/charter/.secrets/dut.env`

4) scripts（測試腳本）
- 以 zip export/import 方式管理（並遵循「同名先刪再匯入」規則）
- 參考：`handoff/migration_scripts.md`

---

## 8) 11F_140 → 11F_131 移植實戰：必帶的「環境化」規則（強烈建議）

> 這段是我們在 11 LAB 實際把平台從 `11F_140(172.14.1.140)` 對齊到 `11F_131(172.14.1.131)` 的結論：
> **平台固定參數要走 systemd env；DUT 變動值走 `dut.env`；script manifest 不要寫死平台參數**。

### 8.1 systemd env（平台固定）
把容易因機器不同而變動、但「對同一台 platform 固定」的值集中到 `charter-worker.service`：

- `CPE_DEV`（USB console port；例如 `/dev/ttyUSB0` 或 `/dev/serial/by-id/...`）
- `PING_IFACE` / `LAN_PARENT_IFACE`（LAN NIC 名稱）
- `WIFI_IFACE`（通常 `wlan0`）
- `PDU_SCRIPT` / `PDU_OUTLET_ID`
- `TEST_PROFILE`

> 這些若寫死在各 script 的 `manifest.yaml`，移植到新機器很容易誤用（例如 `eno2`/`wlx...` 直接把新機搞掛）。

### 8.2 `dut.env`（DUT 變動 / secrets）
把「不該進 zip / 不該進文件站」的 credentials 全部放在：
- `/home/da40/charter/.secrets/dut.env`

例如：`WAREHOUSE_ID/WAREHOUSE_PASSWORD`。

### 8.3 Worker 的 env precedence（避免 manifest 蓋掉 systemd）
移植時必確認：
- worker 合併 env 時，**manifest env 只能當 defaults**，不可覆蓋 systemd（否則會發生 Wi‑Fi iface / LAN iface 被覆蓋）。

### 8.4 Wi‑Fi（Ubuntu 22.04）建議：iwd
- Wi‑Fi 管理建議採 `iwd/iwctl`
- `da40` 建議加入 `netdev`
- 若遇到 DHCP 後沒有 IPv4 default route，建議在工具層（例如 `wifi_iwd.py`）統一補 route，而不是每支 script 各修一次。

---

## 9) 常見問題

- **UI 打得開但 API timeout**：檢查 `charter-api.service` 是否正常、以及 web 是否正確 proxy。
- **worker 不跑/queued 卡住**：檢查 `charter-worker.service`、DB 連線、`/home/da40/charter/data/` 權限。
- **metrics/probe 沒資料**：檢查 `/etc/default/cpe-metrics-agent`、serial device、timer 是否 active。

## 10) 來源筆記（對照 11_26 移植備忘錄）

你先前的移植備忘錄（`11_26移值備忘錄*.txt`）核心步驟是正確的，本文件已吸收並整理成：
- 新 VM/新機器：建立 `da40` 使用者與 `/home/da40/charter/` 目錄結構、安裝依賴（python/venv/postgres/node/pnpm）、建立 Postgres `rg` DB
- 舊機器（controlpc）：打包 `apps/api`、`apps/web`、`tools`、systemd units、`/etc/default/cpe-metrics-agent`、DB dump
- 新機器：解壓、放回目錄、還原 DB、重載 systemd、依順序啟動、做 health check

> 建議：以本文為主，備忘錄僅作為歷史參考。


## 11) 實跑驗證補充（2026-03-02）

- 本文件已在乾淨 Ubuntu 22.04.5 上實跑移植驗證。
- 額外踩雷點與修正：
  1) **DB schema 初始化**：僅建立 role/db 不夠，worker 需要 `runs/scripts/...` 等表。
     - A（乾淨 DB）做法：從來源機器匯出 schema-only 並匯入新機器：
       `pg_dump -s rg > rg_schema.sql` → `psql -d rg -f rg_schema.sql`
  2) **pbr-watchdog**：不同機器網卡名稱不同（controlpc 用 `eno2`），移植時需用 drop-in 覆蓋 `IF`（例如 USB NIC 會是 `enx...`）。
     - 另：`pbr_cpe.py` 非可執行檔，watchdog 腳本需用 `python3 /path/pbr_cpe.py ...`。
