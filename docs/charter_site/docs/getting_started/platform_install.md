# 平台安裝 / 移植

> 本頁說明如何在新機器上安裝 Charter 測試平台。

---

## 📥 下載交付包

### 方式 1：直接下載（推薦）

從 GitHub 下載打包好的檔案：

| 檔案 | 大小 | 用途 |
|------|------|------|
| [charter_api.tar.gz](https://github.com/askeywifisit-ui/charter_project/raw/main/packages/charter_api.tar.gz) | ~30MB | API 程式 |
| [charter_web.tar.gz](https://github.com/askeywifisit-ui/charter_project/raw/main/packages/charter_web.tar.gz) | ~23MB | Web UI 程式 |
| [charter_tools.tar.gz](https://github.com/askeywifisit-ui/charter_project/raw/main/packages/charter_tools.tar.gz) | ~264KB | 工具腳本 |
| [charter_systemd_units.tar.gz](https://github.com/askeywifisit-ui/charter_project/raw/main/packages/charter_systemd_units.tar.gz) | ~618B | Systemd 設定 |

**或從 GitHub 頁面下載**：
https://github.com/askeywifisit-ui/charter_project/tree/main/packages

### 方式 2：從舊機器複製

```bash
# 在舊機器執行
scp -r da40@舊機器IP:/home/da40/charter /home/da40/
```

---

## 🔧 快速安裝步驟

### Step 1：安裝系統依賴

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

# 驗證
node -v
pnpm -v
```

### Step 2：建立使用者

```bash
# 建立 da40 使用者
sudo useradd -m -s /bin/bash da40
sudo usermod -aG sudo da40      # 方便維護
sudo usermod -aG dialout da40   # 序列埠權限
```

### Step 3：設定資料庫

```bash
# 啟動 PostgreSQL
sudo systemctl enable --now postgresql

# 建立資料庫和用戶
sudo -iu postgres psql -c "CREATE USER rg WITH PASSWORD 'rg';"
sudo -iu postgres psql -c "CREATE DATABASE rg OWNER rg;"
sudo -iu postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE rg TO rg;"
```

### Step 4：解壓交付包

```bash
cd ~
mkdir -p charter
tar -xzf charter_api.tar.gz -C charter/
tar -xzf charter_web.tar.gz -C charter/
tar -xzf charter_tools.tar.gz -C charter/
tar -xzf charter_systemd_units.tar.gz -C /etc/systemd/system/
```

### Step 5：匯入資料庫

```bash
# 下載 schema
curl -O https://github.com/askeywifisit-ui/charter_project/raw/main/database/rg_schema_only.sql

# 或從本機
sudo -iu postgres psql -d rg -f rg_schema_only.sql
```

### Step 6：啟動服務

```bash
# 重新載入 systemd
sudo systemctl daemon-reload

# 啟動服務
sudo systemctl enable charter-api charter-web charter-worker cpe-metrics-agent cpe-status-probe
sudo systemctl start charter-api charter-web charter-worker cpe-metrics-agent cpe-status-probe

# 確認服務狀態
sudo systemctl status charter-api charter-web charter-worker cpe-metrics-agent cpe-status-probe
```

---

## 📁 目錄結構

```
/home/da40/charter/
├── apps/
│   ├── api/                   # FastAPI 後端（含 .venv）
│   ├── api_bad_YYYYMMDD_*/  # 舊版 API（備份）
│   ├── web/                  # Vite Web UI（含 node_modules, src/）
│   ├── web_bad_YYYYMMDD_*/ # 舊版 Web（備份）
│   └── web_bak_YYYYMMDD_*/ # 舊版 Web（備份）
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

## 🌐 服務 Port

| 服務 | Port | URL |
|------|------|-----|
| Web UI | 5173 | http://新機器IP:5173 |
| API | 8080 | http://新機器IP:8080 |
| 文件站 | 8000 | http://新機器IP:8000 |

---

## ⚠️ 常見問題

| 問題 | 解決方式 |
|------|----------|
| API 啟動失敗 | `journalctl -u charter-api -n 50` 檢查日誌 |
| DB 連不上 | 確認 Postgres 正常 `sudo systemctl status postgresql` |
| WiFi/Radio 無值 | 確認 cpe-metrics-agent 有 `--with-wifi --with-radio` 參數 |
| 服務 SSH 斷開後停止 | 確認使用 systemd 管理（不是 nohup） |
| CPE Status Disconnected | 確認 cpe_info 正常，檢查網路連線 |

---

## 🔄 服務管理

### 一鍵重啟

```bash
sudo systemctl restart charter-api charter-web charter-worker cpe-metrics-agent cpe-status-probe
```

### 個別服務控制

```bash
sudo systemctl start/stop/restart charter-api
sudo systemctl start/stop/restart charter-web
sudo systemctl start/stop/restart charter-worker
sudo systemctl start/stop/restart cpe-metrics-agent
sudo systemctl start/stop/restart cpe-status-probe
```

---

## 📚 相關頁面

- [下載交付包](../handoff/downloads/)
- [搬家腳本說明](../handoff/migration_scripts/)
- [資料庫初始化](database_setup/)
