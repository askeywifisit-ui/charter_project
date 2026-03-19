# 平台安裝 / 移植（新版）

> 本頁說明如何在新的 Control PC 上安裝 Charter 測試平台。

---

## 🎯 我是誰？

| 問題 | 答案 |
|------|------|
| 這是什麼？ | Charter 自動化測試平台 |
| 誰要做？ | 被移轉的 IT 管理員 |
| 要多久？ | 約 2-3 小時（不含網路問題） |

---

## 📋 前置條件

- Ubuntu 22.04
- 使用者 `da40`（或自行調整）
- 網路正常（能連 GitHub / NOC）
- WiFi 網卡（Broadcom 建議）
- Serial Console 線（USB to Serial）

---

## 快速對照表

| 服務 | Port | 說明 |
|------|------|------|
| Web UI + API Proxy | 5173 | Vite dev server |
| API Backend | 8080 | FastAPI |
| 文件站 | 8000 | MkDocs |

---

## 1️⃣ OS 依賴安裝

```bash
# 更新系統
sudo apt update

# 安裝基本軟體
sudo apt install -y \
  python3 python3-venv python3-pip \
  postgresql postgresql-contrib \
  git unzip curl jq \
  build-essential dkms \
  postgresql-client

# 安裝 Node.js（使用 LTS 版本 20.x 或 22.x）
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# 或使用 22.x
# curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
# sudo apt install -y nodejs

# 安裝 pnpm
npm install -g pnpm

# 驗證
node -v
npm -v
```

（必選）建立使用者並給予權限：
```bash
# 建立 da40 使用者（如果還沒有）
sudo useradd -m -s /bin/bash da40
sudo usermod -aG sudo da40        # 方便維護
sudo usermod -aG dialout da40    # 序列埠權限
```

### PDU 權限設定（重要！）

如果使用 PDU（Power Distribution Unit）控制 CPE 電源，需要設定權限：
```bash
# 確認 PDU 設備
ls -la /dev/ttyUSB*  # 或 /dev/ttyACM*

# 將 da40 加入 PDU 所屬群組（通常是 dialout 或 usb）
sudo usermod -aG dialout da40

# 如果 PDU 使用特定的 USB 埠，可能需要額外設定
# 請根據實際 PDU 型號調整
```

---

## 2️⃣ 資料庫設定

```bash
# 啟動 PostgreSQL
sudo systemctl enable --now postgresql

# 建立資料庫和用戶
sudo -iu postgres psql -c "CREATE USER rg WITH PASSWORD 'rg';"
sudo -iu postgres psql -c "CREATE DATABASE rg OWNER rg;"
sudo -iu postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE rg TO rg;"

# 驗證
psql -h 127.0.0.1 -U rg -d rg -c '\conninfo'
```

---

## 3️⃣ 複製程式碼

### 方法 A：完整搬家打包（推薦）

#### 在舊機器上打包：
```bash
sudo -iu da40
cd /home/da40

mkdir -p charter-migration
cd charter-migration

# 1) 程式與工具
cp -a /home/da40/charter/apps/api ./apps_api
cp -a /home/da40/charter/apps/web ./apps_web
cp -a /home/da40/charter/tools ./tools

# 2) 一鍵腳本
cp /home/da40/charter/restart.all.charter.sh . 2>/dev/null || true
cp /home/da40/charter/log.color.charter.sh . 2>/dev/null || true

# 3) systemd units
sudo cp /etc/systemd/system/charter-api.service .
sudo cp /etc/systemd/system/charter-web.service .
sudo cp /etc/systemd/system/charter-worker.service .
sudo cp /etc/systemd/system/cpe-metrics-agent.service .
sudo cp /etc/systemd/system/cpe-status-probe.service .
sudo cp /etc/systemd/system/pbr-watchdog.service .
sudo cp /etc/systemd/system/cpe-status-probe.timer .

# 4) 環境設定檔
sudo cp /etc/default/cpe-metrics-agent . 2>/dev/null || true

# 5) DB dump（重要！）
sudo -iu postgres pg_dump rg > ./rg_db_dump.sql

# 打包
cd /home/da40/charter-migration
tar czf charter_migration_full.tgz *
```

#### 在新機器上建立目錄結構：
```bash
sudo -iu da40
mkdir -p ~/charter/{apps,tools,data,logs}
mkdir -p ~/charter/apps/{api,web}
```

在舊機器上打包：
```bash
sudo -iu da40
cd /home/da40

mkdir -p charter-migration
cd charter-migration

# 1) 程式與工具
cp -a /home/da40/charter/apps/api ./apps_api
cp -a /home/da40/charter/apps/web ./apps_web
cp -a /home/da40/charter/tools ./tools

# 2) 設定檔與腳本
cp /home/da40/charter/restart.all.charter.sh . 2>/dev/null || true
cp /home/da40/charter/log.color.charter.sh . 2>/dev/null || true

# 3) systemd units
sudo cp /etc/systemd/system/charter-api.service .
sudo cp /etc/systemd/system/charter-web.service .
sudo cp /etc/systemd/system/charter-worker.service .
sudo cp /etc/systemd/system/cpe-metrics-agent.service .
sudo cp /etc/systemd/system/cpe-status-probe.service .
sudo cp /etc/systemd/system/pbr-watchdog.service .
sudo cp /etc/systemd/system/cpe-status-probe.timer .

# 4) 環境設定檔
sudo cp /etc/default/cpe-metrics-agent . 2>/dev/null || true

# 5) DB dump（重要！）
sudo -iu postgres pg_dump rg > ./rg_db_dump.sql

# 打包
cd /home/da40/charter-migration
tar czf charter_migration_full.tgz *
```

把 `charter_migration_full.tgz` 傳到新機器：
```bash
scp charter_migration_full.tgz da40@新機器IP:~
```

在新機器解壓：
```bash
sudo -iu da40
cd ~
tar xzf charter_migration_full.tgz -C .

# 移到正確位置
mkdir -p charter/apps charter/tools
mv apps_api charter/apps/api
mv apps_web charter/apps/web
mv tools charter/tools
mv restart.all.charter.sh charter/ 2>/dev/null || true
mv log.color.charter.sh charter/ 2>/dev/null || true

# 還原資料庫
sudo -iu postgres psql -d rg < ~/rg_db_dump.sql
```

### 方法 B：直接 scp 複製

```bash
# 複製整個 charter 目錄
scp -r da40@舊機器IP:/home/da40/charter /home/da40/
```

### 方法 C：從 GitHub

```bash
cd /home/da40
git clone https://github.com/askeywifisit-ui/charter_project.git charter
```

---

## 4️⃣ 安裝依賴

```bash
# API 依賴
cd /home/da40/charter/apps/api
pip install -r requirements.txt

# Web 依賴
cd /home/da40/charter/apps/web
npm install
# 或 pnpm install
```

---

## 5️⃣ 設定 Secrets

```bash
# 建立 secrets 目錄
mkdir -p /home/da40/charter/.secrets

# 複製或建立設定檔
cp /path/to/noc_profiles.json /home/da40/charter/.secrets/
cp /path/to/dut.env /home/da40/charter/.secrets/

# 編輯設定
nano /home/da40/charter/.secrets/noc_profiles.json
nano /home/da40/charter/.secrets/dut.env
```

> 詳細格式請參考 [Environment Template](../environment_template/)

---

## 6️⃣ 啟動 API + Web 服務

### 建立 Service 檔案

```bash
# API Service
sudo bash -c 'cat > /etc/systemd/system/charter-api.service << EOF
[Unit]
Description=Charter API
After=postgresql.service

[Service]
Type=simple
User=da40
WorkingDirectory=/home/da40/charter/apps/api
Environment="DATABASE_URL=postgresql://rg:rg@localhost:5432/rg"
Environment="PATH=/home/da40/.local/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/da40/.local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
EOF'

# Web Service (Vite)
sudo bash -c 'cat > /etc/systemd/system/charter-web.service << EOF
[Unit]
Description=Charter Web UI
After=network.target

[Service]
Type=simple
User=da40
WorkingDirectory=/home/da40/charter/apps/web
Environment="PATH=/home/da40/.local/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/da40/charter/apps/web/node_modules/.bin/vite --host 0.0.0.0 --port 5173
Restart=always

[Install]
WantedBy=multi-user.target
EOF'
```

### 啟動服務

```bash
# 重載 systemd
sudo systemctl daemon-reload

# 啟用並啟動
sudo systemctl enable charter-api charter-web
sudo systemctl start charter-api charter-web

# 檢查狀態
curl http://127.0.0.1:8080/api/health
# 預期：{"ok":true}
```

---

## 7️⃣ 設定網路（重要！）

### 有線網卡（Control PC 到 CPE）

```bash
# 設定固定 IP（例如 enp3s0 → 192.168.1.2）
sudo ip addr add 192.168.1.2/24 dev enp3s0
```

### WiFi 網卡（測試用）

```bash
# 載入 WiFi 驅動（如果是 Broadcom）
sudo modprobe -r bcma
sudo modprobe wl

# 確認網卡出現
ip link show | grep wlan
```

---

## 8️⃣ 啟動 CPE 監控服務（Dashboard 需要！）

> 這兩個服務是 Dashboard 能顯示資料的關鍵！
> **重要：請用 systemd 管理這些服務**，不要用 nohup（關掉 SSH 就會停止）

### 8.1 建立 Systemd Service

#### CPE Status Probe Service

```bash
sudo bash -c 'cat > /etc/systemd/system/cpe-status-probe.service << EOF
[Unit]
Description=CPE Status Probe
After=network.target

[Service]
Type=simple
User=da40
Environment="PATH=/home/da40/.local/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/da40/charter/apps/api/.venv/bin/python /home/da40/charter/apps/api/cpe_status_probe.py --api http://127.0.0.1:8080 --cpe 192.168.1.1 --wan-iface br-wan --interval 10
Restart=always

[Install]
WantedBy=multi-user.target
EOF'
```

#### CPE Metrics Agent Service

```bash
sudo bash -c 'cat > /etc/systemd/system/cpe-metrics-agent.service << EOF
[Unit]
Description=CPE Metrics Agent
After=network.target

[Service]
Type=simple
User=da40
Environment="PATH=/home/da40/.local/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/da40/charter/apps/api/.venv/bin/python /home/da40/charter/tools/cpe_metrics_agent_serial.py --api http://127.0.0.1:8080 --device /dev/serial/by-id/usb-FTDI_FT232R_USB_UART_B0008Z1P-if00-port0 --baud 115200 --user admin --password YOUR_CPE_PASSWORD --iface br-wan --interval 10 --run-id 0 --with-wifi --with-radio
Restart=always

[Install]
WantedBy=multi-user.target
EOF'
```

### 8.2 啟動服務

```bash
# 重載 systemd
sudo systemctl daemon-reload

# 啟用並啟動
sudo systemctl enable cpe-status-probe cpe-metrics-agent
sudo systemctl start cpe-status-probe cpe-metrics-agent

# 檢查狀態
sudo systemctl status cpe-status-probe --no-pager
sudo systemctl status cpe-metrics-agent --no-pager
```

### 8.3 驗證

```bash
# CPE Status（Internet/Cloud）
curl http://127.0.0.1:8080/api/cpe/status/latest
# 預期：internet: Connected, cloud: Connected

# CPE Metrics（CPU/Memory/Temp）
curl http://127.0.0.1:8080/api/metrics/latest?limit=1
# 預期：有 cpu_pct, mem_pct, temp_c 資料
```

### 8.4 常見問題

| 問題 | 解決方式 |
|------|----------|
| 服務啟動失敗 | `journalctl -u cpe-status-probe -n 50` |
| 服務停止 | `sudo systemctl restart cpe-status-probe` |
| 關掉 SSH 後服務停了 | 確認用 systemd 管理，不是 nohup |

---

## 9️⃣ 驗收

```bash
# API Health
curl http://127.0.0.1:8080/api/health

# CPE Status（Internet/Cloud）
curl http://127.0.0.1:8080/api/cpe/status/latest

# CPE Metrics（CPU/Memory/Temp）
curl http://127.0.0.1:8080/api/metrics/latest?limit=1

# Web UI
curl http://127.0.0.1:5173/
```

成功標準：
- API 回 `{"ok":true}`
- CPE Status 有 `internet: Connected`, `cloud: Connected`
- Metrics 有 `cpu_pct`, `mem_pct`, `temp_c` 資料

---

## 🔄 服務管理（完整版）

> 所有 Charter 平台服務的 systemd 設定與管理方式。

### 服務清單

| 服務名稱 | 說明 | Port |
|---------|------|------|
| charter-api.service | API 後端 | 8080 |
| charter-web.service | Web UI（Vite） | 5173 |
| charter-docs.service | 文件站（MkDocs） | 8000 |
| charter-worker.service | 腳本執行 worker | - |
| cpe-status-probe.service | CPE 狀態探針 | - |
| cpe-status-probe.timer | CPE 狀態探針計時器 | - |
| cpe-metrics-agent.service | CPE Metrics 收集 | - |
| pbr-watchdog.service | PBR 監控（可選） | - |

### 一鍵重啟所有服務

```bash
echo "=== Charter 全系統一鍵重啟程序 ==="

# === Step 1: 停止所有服務 ===
echo "[1/4] 停止 Charter 相關服務..."
sudo systemctl stop charter-web.service || true
sudo systemctl stop cpe-status-probe.service || true
sudo systemctl stop cpe-metrics-agent.service || true
sudo systemctl stop charter-worker.service || true
sudo systemctl stop charter-api.service || true
sudo systemctl stop pbr-watchdog.service || true

# === Step 2: 重新載入 systemd 設定 ===
echo "[2/4] 重新載入 systemd 設定..."
sudo systemctl daemon-reload

# === Step 3: 依正確順序啟動所有服務 ===
echo "[3/4] 啟動 Charter 服務..."
sudo systemctl start charter-api.service
sudo systemctl start charter-worker.service
sudo systemctl start cpe-metrics-agent.service
sudo systemctl start cpe-status-probe.service
sudo systemctl start charter-web.service
sudo systemctl start pbr-watchdog.service

# === Step 4: 顯示服務狀態 ===
echo
echo "[4/4] ✅ Charter 服務當前狀態："
sudo systemctl status \
 charter-api.service \
 charter-worker.service \
 cpe-metrics-agent.service \
 cpe-status-probe.service \
 pbr-watchdog.service \
 charter-web.service --no-pager
```

### 個別服務管理

```bash
# 停止
sudo systemctl stop charter-api.service

# 啟動
sudo systemctl start charter-api.service

# 重啟
sudo systemctl restart charter-api.service

# 查看狀態
sudo systemctl status charter-api.service --no-pager

# 查看日誌
journalctl -u charter-api.service -n 50 -f
```

### 確認服務是否正常

```bash
# API Health
curl http://127.0.0.1:8080/api/health

# CPE Status
curl http://127.0.0.1:8080/api/cpe/status/latest

# Metrics
curl http://127.0.0.1:8080/api/metrics/latest?limit=1

# Worker
ps aux | grep worker | grep -v grep
```

---

## ⚠️ 移植常見問題（已驗證問題 + 解決方案）

> 本節列出從 172.14.1.140 移植到新機器時實際遇到的問題。

---

### 問題 1：API 啟動後 Dashboard 顯示「NO HB」

**原因**：資料庫 schema 不完整，缺少欄位

**解決**：
```bash
sudo -iu postgres psql -d rg << 'SQL'
-- 修復 runs 表
ALTER TABLE runs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT now();
UPDATE runs SET created_at = started_at WHERE created_at IS NULL;

-- 修復 cpe_metrics 表
ALTER TABLE cpe_metrics ADD COLUMN IF NOT EXISTS run_id INTEGER;

-- 修復 cpe_status 表（internet_ok/cloud_ok 需為 boolean）
ALTER TABLE cpe_status ALTER COLUMN internet_ok TYPE boolean USING internet_ok::boolean;
ALTER TABLE cpe_status ALTER COLUMN cloud_ok TYPE boolean USING cloud_ok::boolean;

-- 建立缺少的表格
CREATE TABLE IF NOT EXISTS wifi_radio_state (
    id SERIAL PRIMARY KEY, ts TIMESTAMP NOT NULL DEFAULT now(),
    device_id TEXT, radio TEXT, ssid TEXT, channel INTEGER,
    bandwidth TEXT, tx_power TEXT, status TEXT
);

-- 權限
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO rg;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO rg;
SQL

# 重啟 API
sudo systemctl restart charter-api
```

---

### 問題 2：Dashboard 的 Wi-Fi 和 Radio 欄位空白

**原因**：這些欄位需要 WiFi 介面卡和對應的探針腳本

**狀態**：目前為已知限制，可忽略或實作 `wifi_stations` 功能

---

### 問題 3：CPE Metrics（CPU/Memory/Temp）顯示異常值

**原因**：cpe_metrics_agent 使用的 cpe_console_serial.py 在 pipe 模式下讀取串口異常

**狀態**：已確認問題，但尚待完整修復。目前 Dashboard 需手動 POST 資料或依賴 cpe_status_probe

---

### 問題 4：服務在 SSH 斷開後停止

**原因**：使用 nohup 而非 systemd 管理服務

**解決**：確認所有服務使用 systemd
```bash
sudo systemctl enable cpe-status-probe cpe-metrics-agent
sudo systemctl start cpe-status-probe cpe-metrics-agent
```

---

### 問題 5：CPE Status（Internet/Cloud）持續 Disconnected

**檢查**：
```bash
# 確認 cpe_info 正常
/home/da40/charter/tools/cpe_info

# 確認 cpe_status_probe 在跑
ps aux | grep cpe_status | grep -v grep

# 確認 API 有資料
curl http://127.0.0.1:8080/api/cpe/status/latest | jq '.internet,.cloud'
```

---

### 問題 6：移植後文件站需同步

**原因**：兩個文件站位於不同機器

**解決**：
```bash
# 在本機執行
rsync -avz --delete /Users/csit/.openclaw/workspace/docs/charter_site/site/ \
  da40@172.14.1.200:/home/da40/charter/docs_site/site/
```

---

### 問題 7：腳本執行失敗 - NOC 認證錯誤

**錯誤**：
```
403 Client Error: Forbidden for url: https://piranha-int.tau.dev-charter.net/api/Customers/login
```

**原因**：NOC 憑證無效或過期

**解決**：檢查 `/home/da40/charter/.secrets/noc_profiles.json` 中的憑證是否正確

---

### 問題 8：Worker 未啟動導致腳本排隊不執行

**現象**：腳本一直處於 queued 狀態，Worker 顯示 idle

**原因**：worker.py 未在執行

**解決**：啟動 worker 並設定為 systemd 服務
```bash
sudo bash -c 'cat > /etc/systemd/system/charter-worker.service << EOF
[Unit]
Description=Charter Worker
After=network.target

[Service]
Type=simple
User=da40
WorkingDirectory=/home/da40/charter/apps/api
Environment="PATH=/home/da40/.local/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/da40/charter/apps/api/.venv/bin/python /home/da40/charter/apps/api/worker.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF'

sudo systemctl daemon-reload
sudo systemctl enable charter-worker
sudo systemctl start charter-worker
```

---

## ⚠️ 常見問題

| 問題 | 解決方式 |
|------|----------|
| API 啟動失敗 | 檢查 `journalctl -u charter-api -n 50` |
| Web 起不來 | 檢查 node_modules 是否完整 `npm install` |
| DB 連不上 | 確認 Postgres 正常 `sudo systemctl status postgresql` |
| WiFi 網卡沒出現 | 檢查驅動 `sudo modprobe wl` |
| 權限不足 | 確認 da40 在 dialout 群組 `groups da40` |
| Dashboard 沒資料 | 確認 cpe_status_probe 和 cpe_metrics_agent 在跑 |
| CPE Status 都是 null | 檢查 `/tmp/cpe_status_probe.log` |
| Metrics 都是 null | 檢查 `/tmp/cpe_metrics.log` |

---

## 📞 支援

- 文件站：http://172.14.1.140:8000/
- 相關頁面：[Environment Template](../environment_template/)、[Migration Scripts](../handoff/migration_scripts/)、[資料庫初始化](../getting_started/database_setup/)
