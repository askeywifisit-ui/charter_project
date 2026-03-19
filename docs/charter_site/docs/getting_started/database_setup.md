# 資料庫初始化

> 本頁說明如何在新機器上設定 Charter 平台的資料庫。

---

## 📋 前置準備

### 需要取得的檔案

交付包中包含資料庫 Schema 檔案：

| 交付檔案 | 說明 |
|---------|------|
| `rg_schema_only.sql` | 資料庫結構定義（14KB） |

---

## 🚀 安裝流程

### Step 1️⃣ - 啟動 PostgreSQL

```bash
# 啟動並設定開機啟動
sudo systemctl enable --now postgresql
```

### Step 2️⃣ - 建立資料庫用戶

```bash
# 建立資料庫用戶
sudo -iu postgres psql -c "CREATE USER rg WITH PASSWORD 'rg';"
```

### Step 3️⃣ - 建立資料庫

```bash
# 建立資料庫
sudo -iu postgres psql -c "CREATE DATABASE rg OWNER rg;"
```

### Step 4️⃣ - 匯入 Schema

```bash
# 進入交付包目錄
cd ~/charter/tools  # 或你放置交付檔的位置

# 匯入資料庫結構
sudo -iu postgres psql -d rg -f rg_schema_only.sql
```

---

## ❓ 常見問題

### Q1: `pg_dump: command not found`

```bash
sudo apt install postgresql-client
```

### Q2: `FATAL: role "rg" does not exist`

```bash
# 確認 postgres 已啟動
sudo systemctl status postgresql
```

### Q3: `permission denied for schema public`

```bash
sudo -iu postgres psql -d rg -c "GRANT ALL ON SCHEMA public TO rg;"
```

---

## 🛠️ 一鍵修復（完整版）

如果匯入失敗，執行這個腳本：

```bash
sudo systemctl enable --now postgresql

sudo -iu postgres psql << 'EOF'
-- 建立用戶
DO $$ 
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'rg') THEN
      CREATE USER rg WITH PASSWORD 'rg';
   END IF;
END
$$;

-- 建立資料庫
SELECT 'CREATE DATABASE rg OWNER rg' 
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'rg')\gexec

-- 賦予權限
GRANT ALL PRIVILEGES ON DATABASE rg TO rg;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO rg;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO rg;
EOF

# 匯入 schema（假設檔案在 ~/charter/tools/rg_schema_only.sql）
sudo -iu postgres psql -d rg -f ~/charter/tools/rg_schema_only.sql
```

---

## ✅ 驗證

```bash
# 重啟 API
sudo systemctl restart charter-api

# 測試 API
curl http://127.0.0.1:8080/api/health
```

> 預期結果：`{"ok":true}`

---

## 📂 相關頁面

| 頁面 | 說明 |
|:-----|:-----|
| [🏠 平台安裝](../platform_install/) | 完整安裝流程 |
| [📦 下載交付包](../../handoff/downloads/) | 取得交付檔案 |
