# Charter 測試平台 - 完整研究手冊

> 本檔案是 Charter 測試平台的完整研究，包含站台、服務、腳本的全部資訊
> 
> **最後更新：** 2026-03-31
> **研究人：** Alice (DA40)

---

## 🏠 站台資訊

### 11F_140 主機（控制主機）

| 項目 | 內容 |
|------|------|
| **IP** | 172.14.1.140 |
| **主機名** | controlpc |
| **使用者** | da40 |
| **SSH** | `ssh da40@172.14.1.140` |
| **主要網卡** | eno2 |
| **CPE 網卡** | eno2 (連接到 192.168.1.2) |

### 其他站台

| 站台 | IP | 主要介面 | 用途 |
|------|-----|----------|------|
| 131 | 172.14.1.131 | enx00e04c6809c3 | Charter 測試站 #1 |
| 200 | 172.14.1.200 | enp3s0 | Charter 測試站 #3 |

---

## 🔧 服務狀態

### 目前運行的服務

```bash
systemctl status charter-api charter-web charter-worker cpe-metrics-agent cpe-status-probe pbr-watchdog
```

| 服務 | 狀態 | Port | 用途 |
|------|-------|------|------|
| charter-api | ✅ Running | 8080 | FastAPI 後端 |
| charter-web | ✅ Running | 5173 | Vite 前端 |
| charter-worker | ✅ Running | - | 腳本執行器 |
| cpe-metrics-agent | ✅ Running | - | CPE 監控收集 |
| cpe-status-probe | ✅ Running | - | CPE 狀態探針 |
| pbr-watchdog | ✅ Running | - | PBR 路由維護 |

### 服務上次啟動時間
- 2026-03-29 10:06 (CST)

---

## 🌐 PBR 設定

### 站台差異

| 站台 | 網卡介面 | SRC IP |
|------|----------|--------|
| 131 | enx00e04c6809c3 | 192.168.1.2 |
| 140 | eno2 | 192.168.1.2 |
| 200 | enp3s0 | 192.168.1.2 |

### Override 檔案位置
```
/etc/systemd/system/pbr-watchdog.service.d/override.conf
```

---

## 📦 模組架構

### 三大模組

| 模組 | 路徑 | Port | 框架 |
|------|------|------|------|
| **Web** | `/home/da40/charter/apps/web/` | 5173 | Vite + Node.js |
| **API** | `/home/da40/charter/apps/api/` | 8080 | FastAPI (Python) |
| **Tools** | `/home/da40/charter/tools/` | - | Python / Shell |

### API 資料庫

| 項目 | 值 |
|------|---|
| 資料庫名 | rg |
| 使用者 | rg |
| 密碼 | rg |
| 主機 | 127.0.0.1 |
| Port | 5432 |

---

## 🧪 測試腳本總覽

### 腳本統計

| Suite | 數量 | 用途 |
|-------|------|------|
| **sanity** | 28 | 基本功能測試 |
| **stability** | 11 | 穩定性測試 |
| **regression** | 1 | 迴歸測試 |
| **Total** | **40** | |

---

## 📋 Sanity Suite（基本功能測試）- 28 個

### 網路連線測試

| Script ID | 名稱 | 用途 |
|-----------|------|------|
| 5229 | WLAN_Client_connects_successfully_over_Default_SSID | WiFi 連線測試 |
| 5230 | SSID_broadcast_when_WiFi_radios_toggled | WiFi 廣播測試 |
| 5231 | Router_resolves_the_DNS_queries_using_IPv4 | DNS 查詢 (IPv4) |

### WAN 連線測試

| Script ID | 名稱 | 用途 |
|-----------|------|------|
| 5232 | WAN_IPv4_Connectivity | WAN IPv4 連線 |
| 5233 | WAN_IPv6_Connectivity | WAN IPv6 連線 |

### SSH 測試

| Script ID | 名稱 | 用途 |
|-----------|------|------|
| 5225 | SSH_basic_test | SSH 基本功能 |
| 5226 | SSH_disable_test | SSH 關閉測試 |
| 5235 | SSH_allowed_local_IP_from_LAN_Client | SSH 允許 LAN IP |
| 5236 | SSH_allowed_WAN_IP_from_LAN_Client_profile | SSH 允許 WAN IP |
| 5238 | SSH_not_allowed_wrong_credential | SSH 錯誤密碼拒絕 |
| 5239 | SSH_authorized_only_on_port_22 | SSH 僅限 port 22 |
| 5240 | SSH_only_1_session_per_username | SSH 單一 session |
| 5241 | SSH_should_be_allowed_to_WAN_from_operator_facing_client | SSH WAN 存取 |
| 5253 | SSH_allowed_local_IP_from_WLAN_Client | SSH 允許 WLAN IP |

### WiFi 網頁測試

| Script ID | 名稱 | 用途 |
|-----------|------|------|
| 5243 | Warehouse_Web_Page_should_load_with_IPv4_address_on_LAN | LAN IPv4 存取 |
| 5245 | Warehouse_Web_Page_should_load_with_Domain_Name | 網域名稱存取 |
| 5255 | Warehouse_Web_Page_should_load_with_IPv6_Link_Local_address_on_LAN | LAN IPv6 存取 |
| 5234 | Customer_page_should_load_using_Domain_Name_on_LAN_Client | LAN Client 網頁 |

### UPnP 測試

| Script ID | 名稱 | 用途 |
|-----------|------|------|
| 5242 | Test_Upnp_discovery | UPnP 發現 |
| 5246 | UPnP_State_Changed_From_Disabled_To_Enabled | UPnP 啟用 |
| 5247 | UPnP_State_Changed_From_Enabled_To_Disabled | UPnP 停用 |

### DHCP 保留測試

| Script ID | 名稱 | 用途 |
|-----------|------|------|
| 5248 | Add_DHCP_Reservation | 新增 DHCP 保留 |
| 5249 | Update_DHCP_Reservation | 更新 DHCP 保留 |
| 5250 | Delete_DHCP_Reservation | 刪除 DHCP 保留 |
| 5251 | Factory_Reset_DHCP_Reservation | 重置 DHCP 保留 |
| 5252 | IP_reservation_for_WLAN_connected_clients | WLAN IP 保留 |

### 整合測試

| Script ID | 名稱 | 用途 |
|-----------|------|------|
| 5227 | WIFI_basic_test | WiFi 基本測試 |
| 5228 | NOC_API_basic_test | NOC API 測試 |

---

## ⚡ Stability Suite（穩定性測試）- 11 個

### 循環測試

| Script ID | 名稱 | 用途 |
|-----------|------|------|
| 5259 | Cycle_power_on_off_test | 循環開關機測試 |
| 5116 | Continuously_executing_reboot | 連續重啟測試 |
| 5217 | Continuously_executing_FactoryReset | 連續恢復出廠設定 |

### WiFi 穩定性

| Script ID | 名稱 | 用途 |
|-----------|------|------|
| 5117 | WiFi_radio_enable_disable_longrun | WiFi 開關長時間測試 |
| 5123 | WiFi_radio_enable_disable-xtime | WiFi 開關多次測試 |

### 網路穩定性

| Script ID | 名稱 | 用途 |
|-----------|------|------|
| 5121 | IPv4_Stability_Test_from_LAN_Client | IPv4 LAN 穩定性 |
| 5125 | IPv6_Stability_Test_from_LAN_Client | IPv6 LAN 穩定性 |

### 壓力測試

| Script ID | 名稱 | 用途 |
|-----------|------|------|
| 5119 | Multiple_reboot_stress | 多次重啟壓力測試 |
| 5120 | Multiple_speedtest | 多次速度測試 |
| 5224 | Continuously_executing_speedtest | 連續速度測試 |

### UPnP 長時間測試

| Script ID | 名稱 | 用途 |
|-----------|------|------|
| 5218 | UPNP_enable_disable_longrun | UPnP 開關長時間測試 |

---

## 🔧 Tools 腳本清單

### CPE 相關（8 個）

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

### WiFi 相關（2 個）

| 腳本 | 用途 |
|------|------|
| `wifi_iwd.py` | WiFi IWD 工具 |
| `wifi_nm.py` | WiFi NetworkManager 工具 |

### 網路相關（4 個）

| 腳本 | 用途 |
|------|------|
| `net_probe.py` | 網路探針 |
| `lan_macvlan.py` | LAN MACVLAN 設定 |
| `pbr_cpe.py` | PBR 路由設定 |
| `pbr_cpe_sshpass.py` | PBR SSH 版本 |

### PDU 相關（2 個）

| 腳本 | 用途 |
|------|------|
| `pdu_outlet1.py` | PDU 插座 1 控制 |
| `pdu_outlet2.py` | PDU 插座 2 控制 |

### 其他工具（7 個）

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

## 🌐 對外服務 URL

| 服務 | URL |
|------|-----|
| **文件站（內網）** | http://172.14.1.140:8000 |
| **API** | http://172.14.1.140:8080 |
| **Web UI** | http://172.14.1.140:5173 |
| **文件站（外網）** | https://ground-material-class-listen.trycloudflare.com |

---

## 📂 重要路徑

### 主目錄
- `/home/da40/charter/` - Charter 主目錄

### 程式碼
- `/home/da40/charter/apps/api/` - API 後端
- `/home/da40/charter/apps/web/` - Web 前端
- `/home/da40/charter/tools/` - 工具腳本

### 資料
- `/home/da40/charter/data/scripts/` - 測試腳本
- `/home/da40/charter/data/work/` - 測試輸出日誌

### 設定
- `/home/da40/charter/.secrets/` - 機密設定
- `/etc/default/cpe-metrics-agent` - CPE Agent 設定
- `/etc/systemd/system/charter-api.service.d/10-db.conf` - API 資料庫設定

---

## 🔐 設定檔案

### NOC Profiles
路徑：`/home/da40/charter/.secrets/noc_profiles.json`

**修改後需重啟 charter-worker：**
```bash
sudo systemctl restart charter-worker
```

### DUT 設定
路徑：`/home/da40/charter/.secrets/dut.env`

---

## 🛠️ 常用指令

### 服務管理
```bash
# 查看服務狀態
systemctl status charter-api charter-web charter-worker

# 重啟服務
sudo systemctl restart charter-api
sudo systemctl restart charter-worker

# 查看日誌
journalctl -u charter-api -f
```

### 測試執行
```bash
# 觸發測試
curl -X POST "http://172.14.1.140:8080/api/scripts/5225/run"

# 查看測試列表
curl "http://172.14.1.140:8080/api/runs?limit=50"

# 停止測試
curl -X POST "http://172.14.1.140:8080/api/runs/{run_id}/stop"

# 清除舊測試
curl -X DELETE "http://172.14.1.140:8080/api/runs/purge?older_than_days=0"
```

### 文件站同步
```bash
rsync -avz --delete site/ da40@172.14.1.140:/home/da40/charter/docs_site/site/
```

---

## 📝 版本資訊

| 項目 | 版本/日期 |
|------|-----------|
| Charter Platform | Latest (2026-03) |
| Charter API | FastAPI + Uvicorn |
| Charter Web | Vite + Node.js |
| Python | 3.10+ |
| Node.js | Latest |

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

*本文件由 Alice (DA40) 研究整理*
