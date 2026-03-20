# 搬家腳本說明

> 本頁說明如何使用搬家腳本，將 Charter 平台從舊機器遷移到新機器。

---

## 📋 搬家流程總覽

```
┌─────────────────┐          ┌─────────────────┐
│   舊機器          │          │   新機器          │
│  (172.14.1.140) │          │  (目標主機)      │
└────────┬────────┘          └────────┬────────┘
         │                               │
         │  1️⃣ 執行 Export              │
         │  2️⃣ 傳輸 .tgz              │
         ├──────────────────────────────►│
         │                               │ 3️⃣ 執行 Import
         │                               │ 4️⃣ 匯入 DB
         │                               │ 5️⃣ 啟動服務
```

---

## Step 1️⃣：前置準備

### 確認舊機器環境

- ✅ Charter 服務正常運作
- ✅ 所有腳本存在於 `/home/da40/charter/`
- ✅ PostgreSQL 可連線

### 下載搬家腳本

從文件站下載：
- [charter_migration_export.sh](../../handoff/scripts/charter_migration_export.sh)
- [charter_migration_import.sh](../../handoff/scripts/charter_migration_import.sh)

### 賦予執行權限

```bash
chmod +x charter_migration_export.sh
chmod +x charter_migration_import.sh
```

---

## Step 2️⃣：舊機器匯出

在**舊機器**上執行：

```bash
cd /home/da40/charter
./charter_migration_export.sh
```

### 腳本會自動完成

| 動作 | 說明 |
|:-----|:-----|
| 📦 打包程式碼 | apps/api, apps/web, tools |
| 📁 打包腳本 | data/scripts |
| 🗄️ 匯出 DB Schema | pg_dump --schema-only |
| ⚙️ 打包 Systemd | *.service, *.timer |
| 🔐 計算驗證碼 | SHA256 |

### 產出檔案

```
/home/da40/charter/
├── charter_migration_YYYYMMDD_HHMMSS.tgz      # 搬家包
└── charter_migration_YYYYMMDD_HHMMSS.tgz.sha256  # 驗證碼
```

### 傳輸到新機器

```bash
scp charter_migration_YYYYMMDD_HHMMSS.tgz da40@新機器IP:/home/da40/
```

---

## Step 3️⃣：新機器匯入

### 安裝系統依賴

```bash
sudo apt update
sudo apt install -y \
  python3 python3-venv python3-pip \
  postgresql postgresql-contrib \
  git unzip curl jq \
  build-essential \
  postgresql-client \
  nodejs npm

npm install -g pnpm
```

### 設定資料庫

```bash
sudo systemctl enable --now postgresql

sudo -iu postgres psql << 'EOF'
CREATE USER rg WITH PASSWORD 'rg';
CREATE DATABASE rg OWNER rg;
GRANT ALL PRIVILEGES ON DATABASE rg TO rg;
\q
EOF
```

### 執行匯入腳本

```bash
cd /home/da40
tar -xzf charter_migration_YYYYMMDD_HHMMSS.tgz
chmod +x charter_migration_import.sh
./charter_migration_import.sh
```

---

## Step 4️⃣：複製 Secrets

> ⚠️ 建議重新設定，不要直接用舊的！

```bash
# NOC 設定
nano /home/da40/charter/.secrets/noc_profiles.json

# DUT 設定
nano /home/da40/charter/.secrets/dut.env
```

---

## Step 5️⃣：複製 Systemd 服務

```bash
cd /home/da40
sudo cp /etc/systemd/system/charter-api.service .
sudo cp -r /etc/systemd/system/charter-api.service.d .
sudo cp /etc/systemd/system/charter-web.service .
sudo cp /etc/systemd/system/charter-worker.service .
sudo cp /etc/systemd/system/cpe-metrics-agent.service .
sudo cp /etc/systemd/system/pbr-watchdog.service .
sudo cp /etc/systemd/system/cpe-status-probe.timer .
sudo cp /etc/systemd/system/cpe-status-probe.service .
```

> ⚠️ `charter-api.service.d/` 包含資料庫連線設定（`10-db.conf`），確認內容正確後再啟動服務。

---

## Step 6️⃣：啟動服務

```bash
sudo systemctl daemon-reload
sudo systemctl restart \
  charter-api \
  charter-web \
  charter-worker \
  cpe-metrics-agent \
  cpe-status-probe
```

---

## ✅ 驗證

```bash
# API Health
curl http://127.0.0.1:8080/api/health
# 預期：{"ok":true}

# Systemd 服務
systemctl status charter-api charter-web charter-worker
```

---

## 🔧 服務對照

| 服務 | Port | 用途 |
|:-----|:----:|:-----|
| charter-api | 8080 | API 後端 |
| charter-web | 5173 | Web UI |
| charter-worker | - | 腳本執行器 |
| cpe-metrics-agent | - | CPE 監控 |
| cpe-status-probe | - | CPE 狀態探針 |

---

## ⚠️ 常見問題

| 問題 | 原因 | 解決方式 |
|:-----|:-----|:---------|
| API 502/500 | 服務啟動失敗 | `journalctl -u charter-api -n 50` |
| DB 連不上 | PostgreSQL 未啟動 | `sudo systemctl start postgresql` |
| WiFi 無值 | 缺少參數 | 確認 systemd 有 `--with-wifi --with-radio` |
| CPE Disconnected | 網路問題 | 確認 enp3s0 IP 正確 |

---

## 🔄 緊急回滾

搬家失敗時：

```bash
# 停止新機器服務
sudo systemctl stop charter-api charter-web charter-worker

# 舊機器重啟服務
ssh da40@舊機器IP
sudo systemctl start charter-api charter-web charter-worker
```

---

## 📂 相關頁面

| 頁面 | 說明 |
|:-----|:-----|
| [🏠 平台安裝](../../getting_started/platform_install/) | 完整安裝流程 |
| [📥 下載交付包](../downloads/) | 下載交付包 |
| [🗄️ 資料庫初始化](../../getting_started/database_setup/) | DB 設定與修復 |