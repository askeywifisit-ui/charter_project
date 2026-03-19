# 移植腳本（遷移到新機器）

> 目標：把舊機器的設定/腳本，搬到新機器。

---

## 🎯 我是誰？

| 問題 | 答案 |
|------|------|
| 這是什麼？ | 搬家腳本（Export = 打包，Import = 解開） |
| 誰要做？ | 被移轉的 IT 管理員 |
| 要多久？ | 約 30 分鐘 |

---

## 📥 下載腳本

| 腳本 | 用途 | 下載 |
|------|------|------|
| `charter_migration_export.sh` | 舊機器匯出 | [下載](../handoff/scripts/charter_migration_export.sh) |
| `charter_migration_import.sh` | 新機器匯入 | [下載](../handoff/scripts/charter_migration_import.sh) |

---

## 📦 搬家需要的檔案

### 來源機器（舊）

| 檔案 | 說明 |
|------|------|
| `charter_migration_*.tgz` | 打包好的壓縮檔 |

### 目標機器（新）

| 條件 | 說明 |
|------|------|
| Ubuntu 22.04 | 作業系統 |
| PostgreSQL | 資料庫（見下方安裝） |
| Node.js v22+ | 執行 Vite |
| 網路正常 | 能連網際網路 |

---

## Step 1：匯出（舊機器）

### 1.1 下載腳本

下載 `charter_migration_export.sh` 並放到 `/home/da40/charter/`

### 1.2 執行匯出腳本

```bash
# 放到正確位置
chmod +x /home/da40/charter/charter_migration_export.sh

# 執行（會產生 charter_migration_YYYYMMDD_HHMMSS.tgz）
/home/da40/charter/charter_migration_export.sh
```

### 1.3 產生的檔案

```
charter-migration-YYYYMMDD_HHMMSS/
├── apps/              # API + Web
├── tools/             # 工具腳本
├── scripts/           # 測試腳本
├── charter-api.service # Systemd 服務檔
├── charter-web.service
└── ...
charter_migration_YYYYMMDD_HHMMSS.tgz   ← 壓縮檔
charter_migration_YYYYMMDD_HHMMSS.tgz.sha256  ← 驗證碼
```

### 1.4 搬到新機器

```bash
scp -r charter-migration-YYYYMMDD_HHMMSS da40@新機器IP:/home/da40/
```

---

## Step 2：匯入（新機器）

### 2.1 確認環境

```bash
# 檢查系統
cat /etc/os-release

# 安裝必要軟體
sudo apt update
sudo apt install -y postgresql python3-pip curl jq git
sudo apt install -y nodejs npm
pip install psycopg2-binary fastapi uvicorn
```

### 2.2 安裝 PostgreSQL

```bash
sudo systemctl enable --now postgresql

sudo -iu postgres psql -c "CREATE USER rg WITH PASSWORD 'rg';"
sudo -iu postgres psql -c "CREATE DATABASE rg OWNER rg;"
sudo -iu postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE rg TO rg;"
```

### 2.3 下載並執行腳本

```bash
# 下載 charter_migration_import.sh 並放到 /home/da40/
chmod +x /home/da40/charter_migration_import.sh

# 執行匯入
/home/da40/charter_migration_import.sh /home/da40/charter-migration-YYYYMMDD_HHMMSS/
```

### 2.4 驗證成功

```bash
# 檢查服務狀態
curl http://127.0.0.1:8080/api/health
# 預期：{"ok":true}

curl http://127.0.0.1:5173/api/health
# 預期：{"ok":true}
```

---

## Step 3：設定 Secrets

> **重要**：不要直接用舊的 secrets，要重新設定！

### 3.1 填入 NOC 設定

從舊機器複製或編輯：
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

### 3.2 填入 DUT 設定

```bash
nano /home/da40/charter/.secrets/dut.env
```

格式：
```
WAREHOUSE_ID=YourWarehouseID
WAREHOUSE_PASSWORD=YourPassword
SSH_PASSWORD=YourPassword
```

### 3.3 重啟服務

```bash
sudo systemctl restart charter-api
sudo systemctl restart charter-web
```

---

## ⚠️ 常見問題

| 問題 | 解決方式 |
|------|----------|
| 服務啟動失敗 | 檢查 `journalctl -u charter-api -n 50` |
| 連線失敗 | 確認防火牆開啟 5173/8080/8000 port |
| Secrets 錯誤 | 檢查 `.secrets/noc_profiles.json` 格式 |
| DB 連不到 | 確認 PostgreSQL 正在執行 |

---

## ✅ 交付檢查清單

| 項目 | 確認 |
|------|------|
| API 可連 | `curl http://127.0.0.1:8080/api/health` 回 `{"ok":true}` |
| Web UI 可連 | `curl http://127.0.0.1:5173/` 回 HTML |
| Worker 正常 | `curl http://127.0.0.1:5173/api/runs/worker/status` |
| Secrets 已設定 | `.secrets/noc_profiles.json` 已填入 |
| NOC 可連 | 執行一支測試確認 |

---

## 📞 支援

- 文件站：http://172.14.1.140:8000/
- 相關頁面：[/getting_started/platform_install/](../getting_started/platform_install/)、[/environment_template/](../environment_template/)
