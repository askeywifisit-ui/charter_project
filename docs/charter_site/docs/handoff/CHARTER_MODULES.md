# Charter 平台模組介紹

> 本檔案說明 Charter 測試平台的 Web、API、Tools 模組架構

---

## 📦 三大模組

### 1. Charter Web（前端）

| 項目 | 路徑 |
|------|------|
| 根目錄 | `/home/da40/charter/apps/web/` |
| 框架 | Vite + Node.js |
| Port | 5173 |
| URL | http://172.14.1.140:5173 |

**主要目錄結構：**
```
web/
├── src/              # 原始碼
├── node_modules/     # 依賴套件
├── dist/            # 構建輸出
├── public/          # 靜態資源
└── package.json     # 專案設定
```

---

### 2. Charter API（後端）

| 項目 | 路徑 |
|------|------|
| 根目錄 | `/home/da40/charter/apps/api/` |
| 框架 | FastAPI (Python) |
| Port | 8080 |
| URL | http://172.14.1.140:8080 |
| 資料庫 | PostgreSQL (rg) |

**主要目錄結構：**
```
api/
├── .venv/              # Python 虛擬環境
├── app/                # 應用程式碼
├── requirements.txt     # Python 依賴
└── alembic/            # 資料庫遷移
```

**主要端點：**
- `/api/health` - 健康檢查
- `/api/runs` - 測試執行
- `/api/scripts` - 腳本管理
- `/api/devices` - 設備管理
- `/api/results` - 結果查詢

---

### 3. Charter Tools（工具腳本）

| 項目 | 路徑 |
|------|------|
| 根目錄 | `/home/da40/charter/tools/` |
| 框架 | Python / Shell |

---

## 🔧 Tools 腳本清單

### CPE 相關

| 腳本 | 用途 |
|------|------|
| `cpe_console` | CPE Console 序列埠操控 |
| `cpe_console_serial.py` | CPE Console Python 版 |
| `cpe_info` | CPE 資訊查詢 |
| `cpe_ssh.py` | CPE SSH 操控 |
| `cpe_metrics_agent_serial.py` | CPE Metrics 收集 |
| `cpe_brwan_capture.py` | CPE BR-WAN 抓包 |
| `cpe_capture_role.py` | CPE Role 抓包 |
| `cpe_warehouse_info.py` | CPE Warehouse 資訊 |

### WiFi 相關

| 腳本 | 用途 |
|------|------|
| `wifi_iwd.py` | WiFi IWD 工具 |
| `wifi_nm.py` | WiFi NetworkManager 工具 |

### 網路相鄳

| 腳本 | 用途 |
|------|------|
| `net_probe.py` | 網路探針 |
| `lan_macvlan.py` | LAN MACVLAN 設定 |
| `pbr_cpe.py` | PBR 路由設定 |
| `pbr_cpe_sshpass.py` | PBR SSH 版本 |

### PDU 相關

| 腳本 | 用途 |
|------|------|
| `pdu_outlet1.py` | PDU 插座 1 控制 |
| `pdu_outlet2.py` | PDU 插座 2 控制 |

### 其他工具

| 腳本 | 用途 |
|------|------|
| `cycle_wrapper.py` | Cycle 包裝工具 |
| `serial_lock.py` | Serial 鎖檔管理 |
| `serial_mute.py` | Serial 靜音工具 |
| `log_rename_add_runid.py` | 日誌重新命名 |
| `ssh_awlan_tool.py` | AWLAN SSH 工具 |
| `noc_api_cli.py` | NOC API CLI |
| `collect_cpe_logs.py` | 收集 CPE 日誌 |

---

## 📂 資料庫

| 項目 | 值 |
|------|---|
| 資料庫名 | rg |
| 用戶 | rg |
| 密碼 | rg |
| 主機 | 127.0.0.1 |
| Port | 5432 |

### Schema 匯入

```bash
sudo -iu postgres psql -d rg -f rg_schema_only.sql
```

---

## 🔄 服務重啟順序

若需重啟，建議順序：

```bash
# 1. API 先行
sudo systemctl restart charter-api

# 2. 等 API 啟動後再啟 Worker
sudo systemctl restart charter-worker

# 3. 最後 Web
sudo systemctl restart charter-web
```

---

## 📝 測試腳本位置

| 項目 | 路徑 |
|------|------|
| YAML 腳本 | `/home/da40/charter/data/scripts/` |
| 測試資料 | `/home/da40/charter/data/work/` |
| 日誌輸出 | `/home/da40/charter/var/logs/` |

---

## 🔑 相關設定檔

| 檔案 | 用途 |
|------|------|
| `/home/da40/charter/.secrets/noc_profiles.json` | NOC API 設定 |
| `/home/da40/charter/.secrets/dut.env` | DUT 測試設定 |
| `/etc/default/cpe-metrics-agent` | CPE Agent 設定 |
| `/etc/systemd/system/charter-api.service.d/10-db.conf` | API 資料庫設定 |

---

*最後更新：2026-03-23*
