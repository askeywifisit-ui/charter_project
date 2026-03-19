# 平台安裝 / 移植

> 本頁說明如何在新機器上安裝 Charter 測試平台。

---

## 📥 下載交付包

### 方式 1：從 GitHub 下載 ⭐（推薦）

直接點擊下載：

| 檔案 | 大小 | 說明 |
|:-----|:----:|:-----|
| [📦 charter_api.tar.gz](https://github.com/askeywifisit-ui/charter_project/raw/main/packages/charter_api_20260310_201313.tar.gz) | ~30MB | API 程式 |
| [📦 charter_web.tar.gz](https://github.com/askeywifisit-ui/charter_project/raw/main/packages/charter_web_20260310_201313.tar.gz) | ~23MB | Web UI 程式 |
| [📦 charter_tools.tar.gz](https://github.com/askeywifisit-ui/charter_project/raw/main/packages/charter_tools_20260310_201313.tar.gz) | ~264KB | 工具腳本 |
| [📦 charter_systemd.tar.gz](https://github.com/askeywifisit-ui/charter_project/raw/main/packages/charter_systemd_units_11F_140_20260311_105846.tar.gz) | ~1KB | Systemd 設定 |

> 📌 或從 [GitHub Packages 頁面](https://github.com/askeywifisit-ui/charter_project/tree/main/packages) 下載所有檔案

---

### 方式 2：從舊機器複製

```bash
scp -r da40@舊機器IP:/home/da40/charter /home/da40/
```

---

## 📁 目錄結構

安裝完成後，目錄結構如下：

```
/home/da40/charter/
├── apps/                      # 應用程式
│   ├── api/                   # FastAPI 後端
│   ├── web/                   # Vite Web UI
│   └── web_bak_*/            # 舊版備份
├── tools/                     # 工具腳本
│   ├── cpe_console            # CPE Console（序列埠操控）
│   ├── cpe_console_serial.py  # CPE Console Python 版
│   ├── cpe_info               # CPE 資訊查詢
│   ├── cpe_ssh.py             # CPE SSH 工具
│   ├── cpe_metrics_agent_serial.py  # Metrics 收集
│   ├── wifi_iwd.py            # WiFi iwd 工具
│   ├── wifi_nm.py             # WiFi NetworkManager 工具
│   ├── noc_api_cli.py         # NOC API CLI
│   ├── lan_macvlan.py         # LAN MACVLAN 設定
│   ├── pdu_outlet1.py         # PDU 插座控制
│   ├── pdu_outlet2.py         # PDU 插座控制
│   ├── net_probe.py           # 網路探測
│   ├── collect_cpe_logs.py    # 收集 CPE 日誌
│   ├── ssh_awlan_tool.py      # AWLAN 工具
│   ├── upnp_igd_tester.py     # UPnP IGD 測試
│   └── ...
├── data/                      # 資料
│   └── scripts/               # 測試腳本（YAML manifests）
├── .secrets/                  # 敏感設定（NOC API Key 等）
│   └── noc_profiles.json      # NOC 連線設定
└── var/                       # 執行時產出
    └── logs/                   # 日誌目錄
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
  postgresql-client

# 安裝 Node.js（20.x 或 22.x）
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# 安裝 pnpm
npm install -g pnpm
```

---

### Step 2️⃣ - 建立使用者

```bash
# 建立 da40 使用者
sudo useradd -m -s /bin/bash da40
sudo usermod -aG sudo da40        # 方便維護
sudo usermod -aG dialout da40   # 序列埠權限
```

---

### Step 3️⃣ - 設定資料庫

```bash
# 啟動 PostgreSQL
sudo systemctl enable --now postgresql

# 建立資料庫和用戶
sudo -iu postgres psql -c "CREATE USER rg WITH PASSWORD 'rg';"
sudo -iu postgres psql -c "CREATE DATABASE rg OWNER rg;"
sudo -iu postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE rg TO rg;"
```

---

### Step 4️⃣ - 解壓交付包

```bash
cd ~
mkdir -p charter
tar -xzf charter_api_20260310_201313.tar.gz -C charter/
tar -xzf charter_web_20260310_201313.tar.gz -C charter/
tar -xzf charter_tools_20260310_201313.tar.gz -C charter/
sudo tar -xzf charter_systemd_units_11F_140_20260311_105846.tar.gz -C /etc/systemd/system/
```

---

### Step 5️⃣ - 匯入資料庫

```bash
# 下載 schema
curl -O https://github.com/askeywifisit-ui/charter_project/raw/main/database/rg_schema_only.sql

# 匯入
sudo -iu postgres psql -d rg -f rg_schema_only.sql
```

---

### Step 6️⃣ - 啟動服務

```bash
# 重新載入 systemd
sudo systemctl daemon-reload

# 啟動服務
sudo systemctl enable charter-api charter-web charter-worker cpe-metrics-agent cpe-status-probe
sudo systemctl start charter-api charter-web charter-worker cpe-metrics-agent cpe-status-probe
```

---

## 📁 目錄結構

```
/home/da40/charter/
├── apps/                     # 應用程式
│   ├── api/                # FastAPI 後端
│   ├── web/                # Vite Web UI
│   └── web_bak_*/          # 舊版備份
├── tools/                   # 工具腳本
│   ├── cpe_console        # CPE Console
│   ├── cpe_info           # CPE 資訊
│   ├── cpe_metrics_*      # Metrics 收集
│   └── wifi_*             # WiFi 工具
├── data/                   # 資料
│   └── scripts/           # 測試腳本
├── .secrets/              # 敏感設定
└── var/                   # 執行時產出
```

---

## 🌐 服務 Port 對照

| 服務 | Port | 網址 |
|:-----|:----:|:-----|
| 📱 Web UI | `5173` | http://新機器IP:5173 |
| 🔌 API | `8080` | http://新機器IP:8080 |
| 📖 文件站 | `8000` | http://新機器IP:8000 |

---

## ⚠️ 常見問題

| 問題 | 解決方式 |
|:-----|:---------|
| ❌ API 啟動失敗 | `journalctl -u charter-api -n 50` 檢查日誌 |
| ❌ DB 連不上 | `sudo systemctl status postgresql` |
| ❌ WiFi 無值 | 確認 systemd 有 `--with-wifi --with-radio` |
| ❌ SSH 斷開後停止 | 確認使用 systemd，勿用 nohup |
| ❌ CPE Disconnected | 檢查網路 / cpe_info |

---

## 🔄 服務管理

```bash
# 一鍵重啟
sudo systemctl restart \
  charter-api \
  charter-web \
  charter-worker \
  cpe-metrics-agent \
  cpe-status-probe
```

---

## 📚 相關頁面

| 頁面 | 說明 |
|:-----|:-----|
| [📥 下載交付包](../../handoff/downloads/) | 下載所有打包檔案 |
| [📋 搬家腳本](../../handoff/migration_scripts/) | 詳細搬家流程 |
| [🗄️ 資料庫初始化](../database_setup/) | DB 設定與修復 |