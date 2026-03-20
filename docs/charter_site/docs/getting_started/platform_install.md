# 平台安裝 / 移植

> 本頁說明如何在新機器上安裝 Charter 測試平台。

---

## 💻 系統需求

| 項目 | 需求 |
|:-----|:-----|
| **OS** | Ubuntu 22.04.5 LTS |
| **CPU** | 4 核心以上 |
| **記憶體** | 8GB 以上 |
| **磁碟空間** | 100GB 以上 |

---

## 📥 下載交付包

### 方式 1：從 GitHub 下載（推薦）

| 檔案 | 大小 | 說明 |
|:-----|:----:|:-----|
| [📦 charter_api.tar.gz](https://github.com/askeywifisit-ui/charter_project/raw/main/packages/charter_api_20260310_201313.tar.gz) | ~30MB | API 程式 |
| [📦 charter_web.tar.gz](https://github.com/askeywifisit-ui/charter_project/raw/main/packages/charter_web_20260310_201313.tar.gz) | ~23MB | Web UI 程式 |
| [📦 charter_tools.tar.gz](https://github.com/askeywifisit-ui/charter_project/raw/main/packages/charter_tools_20260310_201313.tar.gz) | ~264KB | 工具腳本 |
| [📦 charter_systemd_units.tar.gz](http://172.14.1.140:8000/assets/systemd/charter_systemd_units_11F_140_20260320.tar.gz) | ~2KB | Systemd 設定 |

### 方式 2：從舊機器複製

```bash
scp -r da40@舊機器IP:/home/da40/charter /home/da40/
```

---

## 📁 目錄結構

```
/home/da40/charter/
├── apps/
│   ├── api/                   # FastAPI 後端（含 .venv）
│   └── web/                  # Vite Web UI（含 node_modules, src/）
├── tools/                     # 工具腳本
│   ├── cpe_console          # CPE Console 工具
│   ├── cpe_console_serial.py
│   ├── cpe_info             # CPE 資訊查詢
│   ├── cpe_metrics_agent_serial.py  # Metrics 收集
│   ├── cpe_ssh.py          # CPE SSH 工具
│   ├── wifi_iwd.py         # WiFi IWD 工具
│   ├── wifi_nm.py          # WiFi NetworkManager 工具
│   ├── noc_api_cli.py      # NOC API CLI
│   ├── pdu_*.py           # PDU 控制腳本
│   ├── lan_macvlan.py      # LAN MACVLAN 工具
│   ├── serial_*.py         # Serial 工具
│   ├── cycle_wrapper.py    # Cycle 包裝工具
│   └── net_probe.py       # 網路探針
├── data/
│   ├── scripts/            # 測試腳本
│   ├── venv/               # Python 虛擬環境
│   └── work/              # 工作目錄
├── .secrets/             # 敏感設定（NOC, DUT 密碼）
├── docs_site/            # 文件站 MkDocs
└── var/                  # 執行時產生的檔案
    ├── serial.lock         # Serial 鎖檔
    └── pdu_mute.log       # PDU 日誌
```

---

## 🔧 安裝流程

### Step 1️⃣ - 安裝系統依賴

```bash
# 更新系統
sudo apt update

# 安裝軟體
sudo apt install -y \
  python3 python3-venv python3-pip \
  postgresql postgresql-contrib \
  git unzip curl jq \
  build-essential \
  postgresql-client \
  nodejs npm

npm install -g pnpm

# 驗證
node -v
pnpm -v
```

### Step 2️⃣ - 建立使用者

```bash
# 建立 da40 使用者
sudo useradd -m -s /bin/bash da40
sudo usermod -aG sudo da40      # 方便維護
sudo usermod -aG dialout da40   # 序列埠權限
```

### Step 3️⃣ - 設定資料庫

```bash
# 啟動 PostgreSQL
sudo systemctl enable --now postgresql

# 建立資料庫和用戶
sudo -iu postgres psql << 'EOF'
CREATE USER rg WITH PASSWORD 'rg';
CREATE DATABASE rg OWNER rg;
GRANT ALL PRIVILEGES ON DATABASE rg TO rg;
\q
EOF
```

### Step 4️⃣ - 解壓交付包

```bash
cd /home/da40
mkdir -p charter
tar -xzf charter_api.tar.gz -C charter/
tar -xzf charter_web.tar.gz -C charter/
tar -xzf charter_tools.tar.gz -C charter/
tar -xzf charter_systemd_units.tar.gz -C /etc/systemd/system/
```

### Step 5️⃣ - 設定 CPE Metrics Agent

> ⚠️ 不同機器的 USB Serial 設備不同！

```bash
# 建立設定檔
sudo nano /etc/default/cpe-metrics-agent
```

內容：
```ini
CPE_AGENT_API=http://127.0.0.1:8080
CPE_BAUD=115200
CPE_USER=root
CPE_IFACE=eth0
INTERVAL=10
RUN_ID=0
WITH_WIFI=1
WITH_RADIO=1
```

| 參數 | 說明 | 備註 |
|------|------|------|
| CPE_SERIAL | USB Serial 設備 | 不設定則自動偵測 |
| CPE_BAUD | 鮑率 | 預設 115200 |
| CPE_IFACE | CPE 設備上的網卡（如 CPE 的 eth0） | 預設 eth0 |

### Step 6️⃣ - 啟動服務

```bash
# 啟動並啟用所有服務
sudo systemctl daemon-reload

sudo systemctl enable \
  charter-api \
  charter-web \
  charter-worker \
  cpe-metrics-agent \
  cpe-status-probe.timer \
  pbr-watchdog

sudo systemctl restart \
  charter-api \
  charter-web \
  charter-worker \
  cpe-metrics-agent \
  cpe-status-probe.timer \
  pbr-watchdog
```

---

## 🌐 服務 Port 對照

| 服務 | Port | URL |
|------|------|-----|
| Web UI | 5173 | http://新機器IP:5173 |
| API | 8080 | http://新機器IP:8080 |
| 文件站 | 8000 | http://新機器IP:8000 |

---

## 🔄 服務管理指令

```bash
# 個別服務控制
sudo systemctl restart charter-api
sudo systemctl restart charter-web
sudo systemctl restart charter-worker
sudo systemctl restart cpe-metrics-agent
sudo systemctl restart cpe-status-probe.timer
sudo systemctl restart pbr-watchdog

# 查看所有服務狀態
sudo systemctl status charter-api charter-web charter-worker cpe-metrics-agent cpe-status-probe.timer pbr-watchdog

# 查看日誌
sudo journalctl -u charter-api -f
sudo journalctl -u charter-web -f
sudo journalctl -u charter-worker -f
sudo journalctl -u cpe-metrics-agent -f
```

---

## 🔧 換環境時需要修改的設定

### 網卡設定（PBR Watchdog）

不同機器的網卡介面不同，修改 `/etc/systemd/system/pbr-watchdog.service.d/override.conf`：

| 機器 | 介面 | SRC IP |
|------|-------|--------|
| 131 | enx00e04c6809c3 | 192.168.1.2 |
| 140 | eno2 | 192.168.1.2 |
| 200 | enp3s0 | 192.168.1.2 |

```bash
# 建立 override 目錄
sudo mkdir -p /etc/systemd/system/pbr-watchdog.service.d

# 編輯設定
sudo nano /etc/systemd/system/pbr-watchdog.service.d/override.conf
```

內容：
```ini
[Service]
Environment="IF=你的網卡"
Environment="SRC=192.168.1.2"
Environment="GW=192.168.1.1"
Environment="SUB=192.168.0/24"
```

### 資料庫設定

修改 `charter-api.service.d/10-db.conf`（如果有）：

```ini
[Service]
Environment=DATABASE_URL=postgresql+psycopg2://rg:rg@127.0.0.1:5432/rg
Environment=PSQL_URL=postgresql://rg:rg@127.0.0.1:5432/rg
```

---

## ⚠️ 常見問題

| 問題 | 解決方式 |
|------|----------|
| 資料庫連線錯誤 | 檢查 PostgreSQL：`sudo systemctl status postgresql` |
| API 無法啟動 | 檢查 `.secrets/noc_profiles.json` 是否存在 |
| Web UI 空白 | 檢查 API 是否正常運作在 port 8080 |
| CPE 無資料 | 檢查 `/etc/default/cpe-metrics-agent` 中的 `CPE_SERIAL` |

---

## ✅ 驗證

```bash
# API Health
curl http://127.0.0.1:8080/api/health
# 預期：{"ok":true}

# 確認所有服務運行
sudo systemctl status charter-api charter-web charter-worker
```

---

## 📌 相關頁面

- [📄 資料庫初始化](database_setup/)
- [📦 下載交付包](../../handoff/downloads/)
- [🔧 移植腳本](../../handoff/migration_scripts/)
