# Charter 測試平台 - 11F_140 完整移交手冊

> 本檔案提供給接手 Charter 測試平台管理的新管理者
> 
> **最後更新：** 2026-03-31
> **維護者：** Alice (DA40)

---

## 📋 快速索引

### 🚀 立即需要知道的

| 項目 | 內容 |
|------|------|
| **文件站（內網）** | http://172.14.1.140:8000 |
| **文件站（外網）** | https://ground-material-class-listen.trycloudflare.com |
| **API 介面** | http://172.14.1.140:8080 |
| **Web UI** | http://172.14.1.140:5173 |
| **GitHub Repo** | https://github.com/askeywifisit-ui/charter_project |
| **站台 SSH** | da40@172.14.1.140 (密碼需向管理者取得) |

### ⚠️ 重要提醒

- 修改 `.secrets/noc_profiles.json` 後需執行：`sudo systemctl restart charter-worker`
- CPE 網路線需插在正確的網卡（eno2）
- 文件站同步指令：`rsync -avz --delete site/ da40@172.14.1.140:/home/da40/charter/docs_site/site/`

---

## 🖥️ 站台概覽

### 11F_140 主機

| 項目 | 內容 |
|------|------|
| **IP** | 172.14.1.140 |
| **主機名** | controlpc |
| **使用者** | da40 |
| **SSH** | `ssh da40@172.14.1.140` |
| **主要網卡** | eno2 (連接 CPE) |

### 其他站台

| 站台 | IP | 主要介面 |
|------|-----|----------|
| 131 | 172.14.1.131 | enx00e04c6809c3 |
| 200 | 172.14.1.200 | enp3s0 |

---

## 🔧 服務管理

### 服務列表

| 服務名稱 | Port | 用途 | 重啟指令 |
|----------|------|------|----------|
| charter-api | 8080 | API 後端 | `sudo systemctl restart charter-api` |
| charter-web | 5173 | Web UI | `sudo systemctl restart charter-web` |
| charter-worker | - | 腳本執行器 | `sudo systemctl restart charter-worker` |
| cpe-metrics-agent | - | CPE 監控收集 | `sudo systemctl restart cpe-metrics-agent` |
| cpe-status-probe.timer | - | CPE 狀態探針 | `sudo systemctl restart cpe-status-probe` |
| pbr-watchdog | - | PBR 路由維護 | `sudo systemctl restart pbr-watchdog` |

### 查看所有服務狀態

```bash
systemctl status charter-api charter-web charter-worker cpe-metrics-agent cpe-status-probe.timer pbr-watchdog
```

### 緊急重啟所有服務

```bash
sudo systemctl restart charter-api charter-web charter-worker cpe-metrics-agent cpe-status-probe pbr-watchdog
```

---

## 🌐 PBR 設定

### 站台差異

每個站台的 PBR 設定不同，因為網卡名稱不同：

| 站台 | 網卡介面 | SRC IP |
|------|----------|--------|
| 131 | enx00e04c6809c3 | 192.168.1.2 |
| 140 | eno2 | 192.168.1.2 |
| 200 | enp3s0 | 192.168.1.2 |

### Override 檔案位置

```
/etc/systemd/system/pbr-watchdog.service.d/override.conf
```

### CPE Metrics Agent 設定

```
/etc/default/cpe-metrics-agent
```

重要參數：
- `CPE_BAUD=115200`
- `WITH_WIFI=1`
- `WITH_RADIO=1`

---

## 📂 重要路徑

### 站台檔案

| 路徑 | 用途 |
|------|------|
| `/home/da40/charter/` | Charter 主目錄 |
| `/home/da40/charter/apps/api/` | API 程式 |
| `/home/da40/charter/apps/web/` | Web UI 程式 |
| `/home/da40/charter/tools/` | 工具腳本 |
| `/home/da40/charter/data/scripts/` | 測試腳本 |
| `/home/da40/charter/data/work/` | 測試輸出日誌 |
| `/home/da40/charter/.secrets/` | 機密設定 |

### 設定檔

| 路徑 | 用途 |
|------|------|
| `/home/da40/charter/.secrets/noc_profiles.json` | NOC API 設定 |
| `/home/da40/charter/.secrets/dut.env` | DUT 測試設定 |
| `/etc/default/cpe-metrics-agent` | CPE Agent 設定 |
| `/etc/systemd/system/charter-api.service.d/10-db.conf` | API 資料庫設定 |

---

## 🧪 測試執行

### 觸發測試

```bash
# 透過 API 觸發
curl -X POST "http://172.14.1.140:8080/api/scripts/{script_id}/run"
```

### 查詢測試結果

```bash
# 取得所有測試
curl "http://172.14.1.140:8080/api/runs?limit=50"

# 取得特定測試
curl "http://172.14.1.140:8080/api/runs/{run_id}"

# 取得測試日誌
curl "http://172.14.1.140:8080/api/runs/{run_id}/log"
```

### 清除舊測試

```bash
# 刪除特定測試
curl -X DELETE "http://172.14.1.140:8080/api/runs/{run_id}"

# 清除所有舊測試（older_than_days=0）
curl -X DELETE "http://172.14.1.140:8080/api/runs/purge?older_than_days=0"
```

### 測試腳本列表

| Suite | Script ID | 說明 |
|-------|-----------|------|
| sanity | 5225-5255 | 基本功能測試 |
| stability | 5116-5259 | 穩定性測試 |

---

## 📚 文件站管理

### 文件站架構

- **MkDocs 原始碼：** `/Users/csit/.openclaw/workspace/docs/charter_site/`
- **GitHub Repo：** `askeywifisit-ui/charter_project`
- **發布目錄：** `/home/da40/charter/docs_site/site/`

### 更新文件站流程

```bash
# 1. 修改文件（Markdown）
cd /Users/csit/.openclaw/workspace/docs/charter_site

# 2. 編譯 MkDocs
python3 -m mkdocs build

# 3. 同步到站台
rsync -avz --delete site/ da40@172.14.1.140:/home/da40/charter/docs_site/site/

# 4. 推送到 GitHub
cd /Users/csit/.openclaw/workspace
git add .
git commit -m "Update documentation"
git push origin main
```

### 外部 Tunnel（臨時）

使用 Cloudflare Quick Tunnel：
```bash
cloudflared tunnel --url http://172.14.1.140:8000
```

---

## 🌐 對外服務

### 目前運行的服务

| 服務 | URL | 狀態 |
|------|-----|------|
| 文件站（內網） | http://172.14.1.140:8000 | ✅ 運行中 |
| API | http://172.14.1.140:8080 | ✅ 運行中 |
| Web UI | http://172.14.1.140:5173 | ✅ 運行中 |

### 外部 Tunnel

- **類型：** Cloudflare Quick Tunnel
- **狀態：** 需手動啟動
- **命令：** `cloudflared tunnel --url http://172.14.1.140:8000`

---

## 🔐 安全設定

### NOC Profiles

路徑：`/home/da40/charter/.secrets/noc_profiles.json`

**修改後必須重啟 charter-worker：**
```bash
sudo systemctl restart charter-worker
```

### Database

| 項目 | 值 |
|------|---|
| 資料庫名 | rg |
| 使用者 | rg |
| 密碼 | rg |
| 主機 | 127.0.0.1 |
| Port | 5432 |

---

## ❓ 常見問題

### Q: API 無回應
```bash
sudo systemctl restart charter-api
```

### Q: Web UI 空白
檢查 charter-api 是否正常：
```bash
curl http://127.0.0.1:8080/api/health
```

### Q: CPE 無資料
檢查序列埠是否連接：
```bash
ls -la /dev/serial/by-id/
```

### Q: 修改 noc_profiles.json 無效
忘記重啟 charter-worker：
```bash
sudo systemctl restart charter-worker
```

---

## 📞 聯絡資訊

| 項目 | 內容 |
|------|------|
| 現任維護者 | Alice (DA40) |
| 站台位置 | 11F |
| GitHub | askeywifisit-ui/charter_project |

---

## 📝 版本歷史

| 日期 | 版本 | 變更 |
|------|------|------|
| 2026-03-31 | 1.0 | 初版建立 |

---

*本文件由 Alice (DA40) 維護*

---

## 📦 Web / API / Tools 模組架構

### 三大模組

| 模組 | 路徑 | Port | 框架 |
|------|------|------|------|
| **Web** | `/home/da40/charter/apps/web/` | 5173 | Vite + Node.js |
| **API** | `/home/da40/charter/apps/api/` | 8080 | FastAPI (Python) |
| **Tools** | `/home/da40/charter/tools/` | - | Python / Shell |

---

### 🔧 Tools 腳本清單

#### CPE 相關
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

#### WiFi 相關
| 腳本 | 用途 |
|------|------|
| `wifi_iwd.py` | WiFi IWD 工具 |
| `wifi_nm.py` | WiFi NetworkManager 工具 |

#### 網路相關
| 腳本 | 用途 |
|------|------|
| `net_probe.py` | 網路探針 |
| `lan_macvlan.py` | LAN MACVLAN 設定 |
| `pbr_cpe.py` | PBR 路由設定 |
| `pbr_cpe_sshpass.py` | PBR SSH 版本 |

#### PDU 相關
| 腳本 | 用途 |
|------|------|
| `pdu_outlet1.py` | PDU 插座 1 控制 |
| `pdu_outlet2.py` | PDU 插座 2 控制 |

#### 其他工具
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

### 📂 API 資料庫

| 項目 | 值 |
|------|---|
| 資料庫名 | rg |
| 使用者 | rg |
| 密碼 | rg |
| 主機 | 127.0.0.1 |
| Port | 5432 |

### Schema 匯入
```bash
sudo -iu postgres psql -d rg -f rg_schema_only.sql
```

---

### 🔄 服務重啟順序

```bash
# 1. API 先行
sudo systemctl restart charter-api

# 2. 等 API 啟動後再啟 Worker
sudo systemctl restart charter-worker

# 3. 最後 Web
sudo systemctl restart charter-web
```

