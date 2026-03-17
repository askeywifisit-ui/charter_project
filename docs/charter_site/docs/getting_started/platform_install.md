# 平台安裝 / 移植

本頁說明如何在新的 Control PC 上安裝 Charter 測試平台。

---

## 前置條件

- Ubuntu 22.04
- 使用者 `da40`（或自行調整）
- 需要下載 4 個交付檔：
  - `charter_api_*.tar.gz`
  - `charter_web_*.tar.gz`
  - `charter_tools_*.tar.gz`
  - `charter_systemd_units_*.tar.gz`

---

## 1️⃣ OS 依賴安裝

```bash
sudo apt update
sudo apt install -y \
  python3 python3-venv python3-pip \
  postgresql postgresql-contrib \
  git unzip curl jq

sudo systemctl enable --now postgresql
```

Web 需要 Node + pnpm：
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g pnpm

node -v
pnpm -v
```

（可選）Serial 權限：
```bash
sudo usermod -aG dialout da40
```

---

## 2️⃣ 解壓程式到固定路徑

```bash
# 建立目錄
sudo mkdir -p /home/da40/charter
sudo chown -R da40:da40 /home/da40/charter

# 解壓交付檔（請替換實際檔名）
cd /home/da40/charter
sudo -u da40 tar -xzf /path/to/charter_api_*.tar.gz
sudo -u da40 tar -xzf /path/to/charter_web_*.tar.gz
sudo -u da40 tar -xzf /path/to/charter_tools_*.tar.gz

# 驗收
ls -la /home/da40/charter/apps/api /home/da40/charter/apps/web /home/da40/charter/tools
```

---

## 3️⃣ 建立資料庫

```bash
sudo -iu postgres psql -c "CREATE USER rg WITH PASSWORD 'rg';" || true
sudo -iu postgres psql -c "CREATE DATABASE rg OWNER rg;" || true
sudo -iu postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE rg TO rg;" || true

# 驗收
psql -h 127.0.0.1 -U rg -d rg -c '\conninfo'
```

---

## 4️⃣ 安裝 systemd units

```bash
# 解壓 unit 到 /etc/systemd/system
sudo tar -xzf /path/to/charter_systemd_units_*.tar.gz -C /etc/systemd

# 重載並啟用
sudo systemctl daemon-reload
sudo systemctl enable --now \
  charter-api.service \
  charter-worker.service \
  charter-web.service \
  cpe-metrics-agent.service \
  cpe-status-probe.timer \
  pbr-watchdog.service
```

---

## 5️⃣ 設定 secrets

```bash
sudo -u da40 mkdir -p /home/da40/charter/.secrets
sudo -u da40 touch /home/da40/charter/.secrets/dut.env
sudo -u da40 touch /home/da40/charter/.secrets/noc_profiles.json
```

> 詳細內容如何填寫，請參考 [Environment Template](/environment_template/)。

---

## 6️⃣ 驗收

```bash
# API Health
curl -fsSL http://127.0.0.1:8080/health

# Web UI + API Health
curl -fsSL http://127.0.0.1:5173/api/health

# Worker Status
curl -fsSL http://127.0.0.1:5173/api/runs/worker/status
```

成功標準：
- API 回 `{"status":"ok"}`
- Worker 回 `{"status":"idle"}` 或 `{"status":"running"}`

---

## 常見問題

| 問題 | 解決方式 |
|------|----------|
| UI 有但 API timeout | `systemctl status charter-api.service` |
| Run 卡住不動 | `systemctl status charter-worker.service` |
| Web 起不來 | 檢查 node/pnpm 是否安裝 |
| DB 連不上 | 確認 Postgres 運作中 + 帳密正確 |
