# 資料庫初始化

> 本頁說明如何正確建立 Charter 平台的資料庫 schema。

---

## ⚠️ 重要：不要手動建 DB！

**問題**：手動建立資料庫很容易漏掉欄位，導致 API 錯誤。

**解決**：從 API 程式自動建立，或從舊機器複製。

---

## 方法 A：從舊機器複製（推薦）

### 1. 在舊機器匯出資料庫

```bash
pg_dump -h 127.0.0.1 -U rg -d rg > charter_db.sql
```

### 2. 在新機器匯入

```bash
sudo -iu postgres psql -d rg -c "DROP DATABASE rg;"
sudo -iu postgres psql -c "CREATE DATABASE rg OWNER rg;"
sudo -iu postgres psql -d rg -f charter_db.sql
```

---

## 方法 B：使用 API 自動建立

API 啟動時會自動建立缺少的欄位。但可能不完整。

啟動 API 後檢查：
```bash
curl http://127.0.0.1:8080/api/health
```

如果有錯誤，檢查日誌：
```bash
journalctl -u charter-api -n 50
```

---

## 常見錯誤與修復

### 錯誤 1：`column runs.created_at does not exist`

**原因**：runs 表缺少 created_at 欄位

**修復**：
```sql
ALTER TABLE runs ADD COLUMN created_at TIMESTAMP DEFAULT now();
UPDATE runs SET created_at = started_at WHERE created_at IS NULL;
```

### 錯誤 2：`column cpe_metrics.run_id does not exist`

**原因**：cpe_metrics 表缺少 run_id 欄位

**修復**：
```sql
ALTER TABLE cpe_metrics ADD COLUMN run_id INTEGER;
```

### 錯誤 3：`relation "cpe_status" does not exist`

**原因**：缺少 cpe_status 表

**修復**：
```sql
CREATE TABLE cpe_status (
    id SERIAL PRIMARY KEY,
    ts TIMESTAMP NOT NULL DEFAULT now(),
    device_id TEXT,
    internet_ok INTEGER,
    cloud_ok INTEGER,
    ipv4 TEXT,
    mac TEXT,
    serial TEXT,
    model TEXT,
    fw TEXT,
    probe_ms INTEGER,
    error TEXT
);
```

---

## 完整 Schema 參考

如果要手動建立，以下是所有需要的表：

### runs
```sql
CREATE TABLE runs (
    id SERIAL PRIMARY KEY,
    script_id INTEGER,
    status TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL DEFAULT now(),
    finished_at TIMESTAMP,
    exit_code INTEGER,
    created_at TIMESTAMP DEFAULT now()
);
```

### scripts
```sql
CREATE TABLE scripts (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    suite TEXT NOT NULL,
    entrypoint TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP,
    zip_path TEXT
);
```

### cpe_metrics
```sql
CREATE TABLE cpe_metrics (
    id SERIAL PRIMARY KEY,
    ts TIMESTAMP NOT NULL DEFAULT now(),
    device_id TEXT,
    cpu_pct DOUBLE PRECISION,
    mem_pct DOUBLE PRECISION,
    temp_c DOUBLE PRECISION,
    rx_mbps DOUBLE PRECISION,
    tx_mbps DOUBLE PRECISION,
    latency_ms DOUBLE PRECISION,
    wifi_clients INTEGER,
    wifi_clients_per_band TEXT,
    run_id INTEGER
);
```

### cpe_status
```sql
CREATE TABLE cpe_status (
    id SERIAL PRIMARY KEY,
    ts TIMESTAMP NOT NULL DEFAULT now(),
    device_id TEXT,
    internet_ok INTEGER,
    cloud_ok INTEGER,
    ipv4 TEXT,
    mac TEXT,
    serial TEXT,
    model TEXT,
    fw TEXT,
    probe_ms INTEGER,
    error TEXT
);
```

### wifi_radio_state
```sql
CREATE TABLE wifi_radio_state (
    id SERIAL PRIMARY KEY,
    ts TIMESTAMP NOT NULL DEFAULT now(),
    device_id TEXT,
    radio TEXT,
    ssid TEXT,
    channel INTEGER,
    bandwidth TEXT,
    tx_power TEXT,
    status TEXT
);
```

### event_log
```sql
CREATE TABLE event_log (
    id SERIAL PRIMARY KEY,
    ts TIMESTAMP NOT NULL DEFAULT now(),
    level VARCHAR(16) NOT NULL,
    message TEXT NOT NULL
);
```

---

## 快速修復腳本

如果遇到 API 錯誤，可以執行這個快速修復：

```bash
sudo -iu postgres psql -d rg << 'SQL'
-- Add missing columns to runs
ALTER TABLE runs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT now();
ALTER TABLE runs ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT now();
ALTER TABLE runs ADD COLUMN IF NOT EXISTS log TEXT;
UPDATE runs SET created_at = started_at WHERE created_at IS NULL;

-- Add missing columns to cpe_metrics
ALTER TABLE cpe_metrics ADD COLUMN IF NOT EXISTS run_id INTEGER;

-- Create or fix cpe_status table
CREATE TABLE IF NOT EXISTS cpe_status (
    id SERIAL PRIMARY KEY,
    ts TIMESTAMP NOT NULL DEFAULT now(),
    device_id TEXT,
    internet_ok boolean,
    cloud_ok boolean,
    ipv4 TEXT,
    mac TEXT,
    serial TEXT,
    model TEXT,
    fw TEXT,
    probe_ms INTEGER,
    error TEXT
);

CREATE TABLE IF NOT EXISTS wifi_radio_state (
    id SERIAL PRIMARY KEY,
    ts TIMESTAMP NOT NULL DEFAULT now(),
    device_id TEXT,
    radio TEXT,
    ssid TEXT,
    channel INTEGER,
    bandwidth TEXT,
    tx_power TEXT,
    status TEXT
);

CREATE TABLE IF NOT EXISTS event_log (
    id SERIAL PRIMARY KEY,
    ts TIMESTAMP NOT NULL DEFAULT now(),
    level VARCHAR(16) NOT NULL,
    message TEXT NOT NULL
);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO rg;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO rg;
SQL
```

---

## 驗證

修復後重啟 API：
```bash
sudo systemctl restart charter-api
```

測試：
```bash
curl http://127.0.0.1:8080/api/health
curl http://127.0.0.1:8080/api/metrics/latest?limit=1
```

---

## 📞 支援

如果遇到其他錯誤，請附上：
- API 日誌：`journalctl -u charter-api -n 50`
- 錯誤訊息
- 嘗試過的修復步驟
