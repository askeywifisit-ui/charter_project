# Charter 測試平台移交檔案

> 本檔案提供給新的 OpenClaw 助理設定參考

---

## 📋 快速索引

| 項目 | 路徑/位置 |
|------|-----------|
| 文件站入口 | http://172.14.1.140:8000 |
| 外網文件站 | https://suspension-seeing-funky-cod.trycloudflare.com |
| GitHub Repo | https://github.com/askeywifisit-ui/charter_project |

---

## 🖥️ 三台測試站台

| 站台 | IP | 用途 | 主要介面 |
|------|-----|------|----------|
| 131 | 172.14.1.131 | Charter 測試站 #1 | enx00e04c6809c3 (USB Ethernet) |
| 140 | 172.14.1.140 | Charter 測試站 #2 + 文件站 | eno2 |
| 200 | 172.14.1.200 | Charter 測試站 #3 | enp3s0 |

---

## 🔧 服務狀態

所有站台皆執行以下服務：

| 服務 | 用途 |
|------|------|
| charter-api | API 後端 (port 8080) |
| charter-web | Web UI (port 5173) |
| charter-worker | 腳本執行器 |
| cpe-metrics-agent | CPE 監控數據收集 |
| cpe-status-probe.timer | CPE 狀態探測定時器 |
| pbr-watchdog | PBR 路由維護 |

### 服務管理指令

```bash
# 查看所有服務狀態
systemctl status charter-api charter-web charter-worker cpe-metrics-agent cpe-status-probe.timer pbr-watchdog

# 重啟服務
sudo systemctl restart charter-api
sudo systemctl restart charter-web
sudo systemctl restart charter-worker
sudo systemctl restart cpe-metrics-agent
sudo systemctl restart cpe-status-probe.timer
sudo systemctl restart pbr-watchdog
```

---

## 🌐 PBR 設定（每站不同）

PBR (Policy-Based Routing) 用於將 CPE LAN 流量導向特定介面。

### 站台設定

| 站台 | 介面 | SRC IP |
|------|------|--------|
| 131 | enx00e04c6809c3 | 192.168.1.2 |
| 140 | eno2 | 192.168.1.2 |
| 200 | enp3s0 | 192.168.1.2 |

### Override 設定檔

路徑：`/etc/systemd/system/pbr-watchdog.service.d/override.conf`

```ini
[Service]
Environment="IF=<介面名稱>"
Environment="SRC=192.168.1.2"
Environment="GW=192.168.1.1"
Environment="SUB=192.168.0/24"
```

### CPE Metrics Agent 設定

路徑：`/etc/default/cpe-metrics-agent`

```ini
CPE_AGENT_API=http://127.0.0.1:8080
CPE_BAUD=115200
CPE_USER=root
CPE_IFACE=eth0
INTERVAL=10
RUN_ID=0
WITH_WIFI=1
WITH_RADIO=1
```

---

## 📂 交付包（從 140 下載）

| 檔案 | 大小 | 說明 |
|------|------|------|
| charter_api.tar.gz | ~30MB | API 程式 |
| charter_web.tar.gz | ~23MB | Web UI 程式 |
| charter_tools.tar.gz | ~264KB | 工具腳本 |
| charter_systemd_units.tar.gz | ~2KB | Systemd 設定檔 |

下載位置：
- **內網**：http://172.14.1.140:8000/assets/packages/
- **外網**：https://suspension-seeing-funky-cod.trycloudflare.com/assets/packages/

---

## 🔐 GitHub Repo 存取

| 項目 | 內容 |
|------|------|
| Repo | askeywifisit-ui/charter_project |
| 狀態 | **Private** |
| 下載帳號 | `testcharter` |
| 下載密碼 | `Askey#*c1234` |

### Release 下載

所有程式包皆在 Release v1.0.0：
https://github.com/askeywifisit-ui/charter_project/releases/tag/v1.0.0

---

## 📚 文件站

文件站由 MkDocs 產生，原始碼在：

`/home/da40/charter/docs_site/`

### 常用指令

```bash
# 編譯文件
cd /home/da40/charter/docs_site
python3 -m mkdocs build

# 啟動文件站（開發模式）
mkdocs serve --dev-addr 0.0.0.0:8000

# 同步到遠端（需 SSH key）
rsync -avz --delete site/ user@remote:/path/to/site/
```

---

## 🤖 Telegram Bot 設定

每個站台有獨立的 Telegram Bot：

| 站台 | Bot Username |
|------|--------------|
| 131 | @DA40_131_Bot |
| 140 | @DA40_140_Bot |
| 200 | @DA40_200_Bot |

### Bot 設定位置

- Bot Token：OpenClaw 設定檔
- Chat ID：與 Bot 對話時自動設定

### OpenClaw 設定檔

路徑：`~/.openclaw/`

---

## 🔑 SSH 存取

### 目前已設定的 SSH Key

| 機器 | SSH User | Host Alias |
|------|----------|------------|
| 172.14.1.131 | root | - |
| 172.14.1.140 | da40 | - |
| 172.14.1.200 | da40 | - |
| 100.40.1.209 (Lina) | da40_llmcda40da40 | lina |

### SSH Config 範例

```
Host lina
 HostName 100.40.1.209
 User da40_llmcda40da40
 IdentityFile ~/.ssh/id_ed25519
 PreferredAuthentications publickey
```

---

## 📝 常用 Systemd 服務路徑

| 服務 | 路徑 |
|------|------|
| charter-api | /etc/systemd/system/charter-api.service |
| charter-web | /etc/systemd/system/charter-web.service |
| charter-worker | /etc/systemd/system/charter-worker.service |
| cpe-metrics-agent | /etc/systemd/system/cpe-metrics-agent.service |
| cpe-status-probe | /etc/systemd/system/cpe-status-probe.service |
| pbr-watchdog | /etc/systemd/system/pbr-watchdog.service |

---

## ⚠️ 重要注意事項

1. **CPE Serial**：`/etc/default/cpe-metrics-agent` 中 `CPE_SERIAL` 若註解，會自動偵測
2. **PBR**：更換站台時需修改對應的網卡介面設定
3. **GitHub Private**：所有交付包需登入 GitHub 才能下載
4. **共用 Telegram**：131/140/200 共用一個 Telegram 帳號收發訊息

---

## 📞 聯絡方式

如有問題，請聯繫：

- **DA40** (本文件作者)
- 站台 IP：172.14.1.131 / 172.14.1.140 / 172.14.1.200
- 外網：http://172.14.1.140:8000

---

*最後更新：2026-03-23*
