# 資料庫初始化

> 本頁說明如何在新機器上設定 Charter 平台的資料庫。

---

## 🚀 快速開始

### 方式 1：從 GitHub 下載 ⭐（推薦）

```bash
# 下載 schema
curl -O https://github.com/askeywifisit-ui/charter_project/raw/main/database/rg_schema_only.sql

# 匯入資料庫
sudo -iu postgres psql -d rg -f rg_schema_only.sql
```

### 方式 2：從舊機器複製

```bash
# 在舊機器匯出
pg_dump -h 127.0.0.1 -U rg -d rg --schema-only > rg_schema.sql

# 傳到新機器後匯入
sudo -iu postgres psql -d rg -f rg_schema.sql
```

---

## ❓ 為什麼需要這個？

新機器需要相同的資料庫結構（Schema）才能讓 Charter API 正常運作。

| 項目 | 說明 |
|:-----|:-----|
| ✅ Schema | 表格結構（需要） |
| ❌ 資料 | 測試資料（不需要） |

---

## ⚠️ 常見錯誤

### 錯誤 1：`column runs.created_at does not exist`

```bash
sudo -iu postgres psql -d rg << 'EOF'
ALTER TABLE runs ADD COLUMN created_at TIMESTAMP DEFAULT now();
ALTER TABLE runs ADD COLUMN updated_at TIMESTAMP DEFAULT now();
ALTER TABLE runs ADD COLUMN log TEXT;
UPDATE runs SET created_at = started_at WHERE created_at IS NULL;
EOF
```

### 錯誤 2：`column cpe_metrics.run_id does not exist`

```bash
sudo -iu postgres psql -d rg -c "ALTER TABLE cpe_metrics ADD COLUMN run_id INTEGER;"
```

### 錯誤 3：`column cpe_status.internet_ok` 類型錯誤

```bash
sudo -iu postgres psql -d rg << 'EOF'
ALTER TABLE cpe_status ALTER COLUMN internet_ok TYPE boolean USING internet_ok::boolean;
ALTER TABLE cpe_status ALTER COLUMN cloud_ok TYPE boolean USING cloud_ok::boolean;
EOF
```

---

## 🛠️ 一鍵修復（推薦）

遇到任何資料庫錯誤，執行這個：

```bash
sudo -iu postgres psql -d rg << 'EOF'

-- runs 表
ALTER TABLE runs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT now();
ALTER TABLE runs ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT now();
ALTER TABLE runs ADD COLUMN IF NOT EXISTS log TEXT;

-- cpe_metrics 表
ALTER TABLE cpe_metrics ADD COLUMN IF NOT EXISTS run_id INTEGER;

-- cpe_status 表
CREATE TABLE IF NOT EXISTS cpe_status (
    id SERIAL PRIMARY KEY,
    ts TIMESTAMP NOT NULL DEFAULT now(),
    device_id TEXT,
    internet_ok boolean,
    cloud_ok boolean,
    ipv4 TEXT, mac TEXT, serial TEXT,
    model TEXT, fw TEXT,
    probe_ms INTEGER, error TEXT
);

-- wifi_radio_state 表
CREATE TABLE IF NOT EXISTS wifi_radio_state (
    id SERIAL PRIMARY KEY,
    ts TIMESTAMP NOT NULL DEFAULT now(),
    device_id TEXT, radio TEXT, ssid TEXT,
    channel INTEGER, bandwidth TEXT,
    tx_power TEXT, status TEXT
);

-- event_log 表
CREATE TABLE IF NOT EXISTS event_log (
    id SERIAL PRIMARY KEY,
    ts TIMESTAMP NOT NULL DEFAULT now(),
    level VARCHAR(16) NOT NULL,
    message TEXT NOT NULL
);

-- 權限
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO rg;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO rg;
EOF
```

---

## ✅ 驗證

```bash
# 重啟 API
sudo systemctl restart charter-api

# 測試
curl http://127.0.0.1:8080/api/health
```

> 預期結果：`{"ok":true}`

---

## 📂 相關頁面

| 頁面 | 說明 |
|:-----|:-----|
| [🏠 平台安裝](../platform_install/) | 完整安裝流程 |
| [📥 下載交付包](../../handoff/downloads/) | 下載所有檔案 |