# 搬家腳本使用指南

> 本頁說明如何使用搬家腳本，將 Charter 平台從舊機器遷移到新機器。

---

## 搬家流程總覽

```
舊機器 (172.14.1.140)          新機器 (目標)
      │                              │
      ├── 執行 Export 腳本 ────────► │
      │   (產生 .tgz 檔案)            │
      │                              ├── 執行 Import 腳本
      │                              ├── 匯入資料庫
      │                              └── 啟動服務
      │
      └── 打包 secrets ─────────────► │  (手動複製)
```

---

## Step 1：前置準備

### 1.1 確認舊機器環境

搬家前，請確認舊機器的：
- Charter 服務正常運作
- 所有腳本存在於 `/home/da40/charter/`
- PostgreSQL 可連線

### 1.2 下載搬家腳本

從文件站下載：
- [charter_migration_export.sh](../handoff/scripts/charter_migration_export.sh) - 匯出腳本
- [charter_migration_import.sh](../handoff/scripts/charter_migration_import.sh) - 匯入腳本

### 1.3 賦予執行權限

```bash
chmod +x charter_migration_export.sh
chmod +x charter_migration_import.sh
```

---

## Step 2：舊機器匯出

### 2.1 執行匯出腳本

在**舊機器**上執行：

```bash
cd /home/da40/charter
./charter_migration_export.sh
```

### 2.2 腳本會自動完成

| 動作 | 說明 |
|------|------|
| 打包程式碼 | apps/api, apps/web, tools |
| 打包腳本 | data/scripts |
| 匯出 DB Schema | pg_dump --schema-only |
| 打包 Systemd 設定 | *.service, *.timer |
| 計算驗證碼 | SHA256 |

### 2.3 產出檔案

執行後會產生：

```
/home/da40/charter/
├── charter_migration_YYYYMMDD_HHMMSS.tgz      # 搬家包（約 1-2 GB）
└── charter_migration_YYYYMMDD_HHMMSS.tgz.sha256  # 驗證碼
```

### 2.4 傳輸到新機器

```bash
scp charter_migration_YYYYMMDD_HHMMSS.tgz da40@新機器IP:/home/da40/
```

---

## Step 3：新機器匯入

### 3.1 安裝系統依賴

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

# 安裝 pnpm
npm install -g pnpm
```

### 3.2 設定資料庫

```bash
# 啟動 PostgreSQL
sudo systemctl enable --now postgresql

# 建立資料庫
sudo -iu postgres psql << 'EOF'
CREATE USER rg WITH PASSWORD 'rg';
CREATE DATABASE rg OWNER rg;
GRANT ALL PRIVILEGES ON DATABASE rg TO rg;
\q
EOF
```

### 3.3 執行匯入腳本

```bash
cd /home/da40
tar -xzf charter_migration_YYYYMMDD_HHMMSS.tgz
chmod +x charter_migration_import.sh
./charter_migration_import.sh
```

### 3.4 匯入腳本會自動完成

| 動作 | 說明 |
|------|------|
| 解壓到正確目錄 | ~/charter/apps, ~/charter/tools |
| 安裝 Python 依賴 | requirements.txt |
| 安裝 Node 依賴 | npm install |
| 匯入資料庫 | pg_dump --schema-only |
| 複製 Systemd 檔 | 到 /etc/systemd/system/ |
| 啟用服務 | systemctl enable |

---

## Step 4：複製 Secrets

> ⚠️ 建議重新設定，不要直接用舊的！

### 4.1 NOC 設定

```bash
nano /home/da40/charter/.secrets/noc_profiles.json
```

格式：
```json
{
  "SPECTRUM_INT": {
    "base": "https://piranha-int.tau.dev-charter.net",
    "email": "your-email@example.com",
    "password": "your-password"
  }
}
```

### 4.2 DUT 設定

```bash
nano /home/da40/charter/.secrets/dut.env
```

格式：
```
WAREHOUSE_ID=YourWarehouseID
WAREHOUSE_PASSWORD=YourPassword
SSH_PASSWORD=YourPassword
```

### 4.3 重啟服務

```bash
sudo systemctl restart charter-api
sudo systemctl restart charter-web
```

---

## Step 5：驗證

### 5.1 檢查服務狀態

```bash
# API
curl http://127.0.0.1:8080/api/health
# 預期：{"ok":true}

# Web UI
curl http://127.0.0.1:5173/
# 預期：HTML 頁面
```

### 5.2 檢查 Systemd 服務

```bash
systemctl status charter-api charter-web charter-worker cpe-metrics-agent cpe-status-probe
```

### 5.3 檢查 CPE 連線

```bash
/home/da40/charter/tools/cpe_info
# 預期：顯示 CPE 資訊
```

---

## 服務對照表

| 服務名稱 | Port | 用途 |
|---------|------|------|
| charter-api | 8080 | API 後端 |
| charter-web | 5173 | Web UI |
| charter-worker | - | 腳本執行器 |
| cpe-metrics-agent | - | CPE 監控 |
| cpe-status-probe | - | CPE 狀態探針 |

---

## 常見問題

| 問題 | 原因 | 解決方式 |
|------|------|----------|
| API 502/500 | 服務啟動失敗 | `journalctl -u charter-api -n 50` |
| DB 連不上 | PostgreSQL 未啟動 | `sudo systemctl start postgresql` |
| Secrets 錯誤 | 格式錯誤 | 檢查 JSON/YAML 語法 |
| WiFi 無值 | 缺少參數 | 確認 systemd 有 `--with-wifi --with-radio` |
| CPE Disconnected | 網路問題 | 確認 enp3s0 IP 正確 |

---

## 緊急回滾

如果搬家失敗，回到舊機器：

```bash
# 停止新機器服務
sudo systemctl stop charter-api charter-web charter-worker

# 舊機器重啟服務
ssh da40@舊機器IP
sudo systemctl start charter-api charter-web charter-worker
```

---

## 📂 相關檔案

| 檔案 | 說明 |
|------|------|
| platform_install.md | 完整安裝流程 |
| database_setup.md | 資料庫初始化 |
| downloads.md | 下載交付包 |
