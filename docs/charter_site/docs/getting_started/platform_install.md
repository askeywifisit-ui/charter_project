# Charter 測試平台安裝 / 移植（systemd 版）

本頁目的：讓同事照著做，就能在一台新的 control PC（Ubuntu 22.04）完成 Charter 平台的 **安裝 → 設定 → systemd 長駐 → 健康檢查**。

> 原則：**平台固定參數走 systemd env / EnvironmentFile；敏感資訊走 `.secrets/`；script manifest 不寫死平台參數。**

---

## 0) 範圍與前提

- **目標機器**：Control PC（平台機）
- **建議 OS**：Ubuntu 22.04 LTS（jammy）
- **標準帳號**：`da40`（需 sudo）
- **平台根目錄**（建議一致）：`/home/da40/charter/`

本頁涵蓋：
- web / api / worker / probe / metrics / watchdog（systemd 服務）

不涵蓋：
- DUT/CPE 接線與測試細節（見 Environment Template / Test Suites）

---

## 1) 元件與埠口

| 元件 | systemd unit | 作用 | 預設埠 |
|---|---|---|---|
| Web | `charter-web.service` | UI（同源呼叫 `/api/...`） | `5173` |
| API | `charter-api.service` | FastAPI + Uvicorn（`/api/...`） | `8080` |
| Worker | `charter-worker.service` | run 任務執行（解壓 zip、pip install、執行腳本、產出 log/archive） | - |
| CPE metrics agent | `cpe-metrics-agent.service` | 採集 CPE metrics → API | - |
| CPE status probe | `cpe-status-probe.timer` + `cpe-status-probe.service` | 定期 probe CPE 狀態 → DB | - |
| PBR watchdog | `pbr-watchdog.service` | 監控/重設 PBR（避免測試路由飄） | - |

UI 通常使用：`http://<CONTROL_PC_IP>:5173`

---

## 2) 目錄結構（建議）

- 平台根：`/home/da40/charter/`
- Web：`/home/da40/charter/apps/web/`
- API/Worker：`/home/da40/charter/apps/api/`
- Tools：`/home/da40/charter/tools/`
- Secrets：`/home/da40/charter/.secrets/`（**不要進 repo**；例如 `noc_profiles.json`、`dut.env`）
- Data：`/home/da40/charter/data/`（runs/work/scripts/venv）

---

## 3) 安裝 OS 依賴（Ubuntu 22.04）

### 3.1 系統套件

```bash
sudo apt update
sudo apt install -y \
  python3 python3-venv python3-pip \
  postgresql postgresql-contrib \
  git unzip curl jq

sudo systemctl enable --now postgresql
```

### 3.2 Node.js + pnpm（Web 用）

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g pnpm

node -v
pnpm -v
```

### 3.3 權限（serial / dialout）

若 metrics / 測試會用到 serial（`/dev/ttyUSB0` 或 `/dev/serial/by-id/...`）：

```bash
sudo usermod -aG dialout da40
# 需要登出再登入才生效
```

---

## 4) 安裝平台程式（Web / API / Tools）

> 交付包建議來源：GitHub `packages/`（或你們內部發佈管道）。

### 4.1 解壓到固定路徑

假設你已取得三個 tar.gz：
- `charter_api_<timestamp>.tar.gz`
- `charter_web_<timestamp>.tar.gz`
- `charter_tools_<timestamp>.tar.gz`

```bash
sudo mkdir -p /home/da40/charter
sudo chown -R da40:da40 /home/da40/charter

cd /home/da40/charter

# API
tar -xzf /path/to/charter_api_<ts>.tar.gz
# 會解出 api/...（依交付包內結構）

# Web
tar -xzf /path/to/charter_web_<ts>.tar.gz

# Tools
tar -xzf /path/to/charter_tools_<ts>.tar.gz
```

完成後請確認（路徑對齊 systemd unit）：
- `/home/da40/charter/apps/api/`（或你們 unit 設定的實際路徑）
- `/home/da40/charter/apps/web/`
- `/home/da40/charter/tools/`

> 若交付包解出來的目錄名不同（例如 `api/app/...` / `web/...` / `tools/...`），請以你們 systemd unit 的 `WorkingDirectory/ExecStart` 為準調整擺放位置。

---

## 5) DB（Postgres）建立與初始化

平台依賴 Postgres。

- **Lab 預設（11F_140 一致）**：DB user/pass 使用 `rg/rg`、DB name 使用 `rg`。
- 注意：本頁只避免寫 **NOC** 帳密；DB `rg/rg` 屬於 lab 預設值（可依環境調整）。

### 5.1 建立 role/db（lab 預設：rg/rg）

```bash
sudo -iu postgres
psql -c "CREATE USER rg WITH PASSWORD 'rg';" || true
psql -c "CREATE DATABASE rg OWNER rg;" || true
psql -c "GRANT ALL PRIVILEGES ON DATABASE rg TO rg;" || true
exit

# 驗證可登入
psql -h 127.0.0.1 -U rg -d rg -c '\\conninfo'
```

### 5.2 Schema 初始化（乾淨環境必做）

兩種做法擇一：

- **A) schema-only 匯入（最常用）**
  - 從來源機器匯出：`pg_dump -s <DB_NAME> > schema.sql`
  - 在新機器匯入：

```bash
psql -h 127.0.0.1 -U <DB_USER> -d <DB_NAME> -f schema.sql
```

- **B) 完整 DB 還原（要保留 runs/history 才需要）**
  - `pg_dump -Fc ...` → `pg_restore -d ...`

---

## 6) Secrets（必做：避免帳密進 repo/文件站）

建議建立：

```bash
sudo mkdir -p /home/da40/charter/.secrets
sudo chown -R da40:da40 /home/da40/charter/.secrets
chmod 700 /home/da40/charter/.secrets
```

常見 secrets：
- `noc_profiles.json`（NOC profile）
- `dut.env`（WAREHOUSE / SSH / 任何敏感值）

權限建議：
```bash
chmod 600 /home/da40/charter/.secrets/*
```

---

## 7) systemd units（長駐與開機自動恢復）

### 7.1 需要的 unit 清單

把以下檔案移植到新機器：

- `/etc/systemd/system/charter-api.service`
- `/etc/systemd/system/charter-worker.service`
- `/etc/systemd/system/charter-web.service`
- `/etc/systemd/system/cpe-metrics-agent.service`
- `/etc/systemd/system/cpe-status-probe.service`
- `/etc/systemd/system/cpe-status-probe.timer`
- `/etc/systemd/system/pbr-watchdog.service`

以及（如有）drop-in：
- `/etc/systemd/system/charter-api.service.d/*.conf`
- `/etc/systemd/system/charter-worker.service.d/*.conf`

### 7.2 服務啟動順序（建議）

```bash
sudo systemctl daemon-reload

# 先 API
sudo systemctl enable --now charter-api.service

# 再 worker
sudo systemctl enable --now charter-worker.service

# 再 metrics/probe
sudo systemctl enable --now cpe-metrics-agent.service
sudo systemctl enable --now cpe-status-probe.timer

# 再 web / watchdog
sudo systemctl enable --now charter-web.service
sudo systemctl enable --now pbr-watchdog.service
```

> `enable` 的目的：**reboot 後會自動起來**。

---

## 8) 健康檢查（移植後必跑）

### 8.1 API / Web

```bash
# API health
curl -fsSL http://127.0.0.1:8080/health

# Web 同源 API health
curl -fsSL http://127.0.0.1:5173/api/health
```

### 8.2 Worker

```bash
curl -fsSL http://127.0.0.1:5173/api/runs/worker/status | python3 -m json.tool
systemctl status charter-worker.service --no-pager
```

---

## 9) 常見問題（Troubleshooting）

- **Web 打得開但 `/api/...` timeout**：
  - 檢查 `charter-api.service`、以及 web 的 proxy/同源設定

- **run queued 卡住 / worker 不跑**：
  - `systemctl status charter-worker.service`
  - DB 連線（`DATABASE_URL`）
  - `/home/da40/charter/data/` 權限

- **probe/metrics 沒資料**：
  - `systemctl status cpe-status-probe.timer cpe-metrics-agent.service`
  - serial device 權限與 `/etc/default/cpe-metrics-agent`

---

## 9.5) 安裝完成後：環境配置（必做）

平台 service 起來後，下一步就是把「環境變動值」填齊（網卡/CPE/NOC profiles/secrets）。請依序看：

1) [Environment Template（哪些欄位要替換）](../environment_template.md)
2) [NOC profile / secrets（放哪裡、權限、template）](../handoff/noc_profile_secrets.md)
3) [交付環境表（同事照填）](../handoff/handoff_env_form.md)
4) [Network iface 指南（最常踩雷）](../handoff/network_iface_guide.md)
5) 驗證：
   - [Quick Start（10 分鐘確認平台可用）](quick_start.md)
   - [驗證步驟（快速驗證）](../handoff/handoff_validation.md)

---

## 10) 移植實戰規則（11F_140 → 11F_131 結論）

> 這段是實戰結論，強烈建議遵循：

1) **平台固定參數 → systemd env**（例如 `WIFI_IFACE/LAN_PARENT_IFACE/PING_IFACE/CPE_DEV/PDU_*`）
2) **DUT 變動 / 敏感 → `/home/da40/charter/.secrets/dut.env`**
3) **script manifest 只補 defaults，不可覆蓋 systemd env**（避免移植後 iface 被蓋錯）
