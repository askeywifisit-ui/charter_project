# Platform Links（平台入口）

本頁提供 Charter 測試平台（http://172.14.1.140:5173）的常用入口。

---

## 🎯 常用入口

| 服務 | URL | 說明 |
|------|-----|------|
| **Web UI** | http://172.14.1.140:5173 | 腳本管理、執行、查看結果 |
| **API Base** | http://172.14.1.140:5173/api | API 端點 |
| **Health Check** | http://172.14.1.140:5173/api/health | API 健康狀態 |
| **Worker Status** | http://172.14.1.140:5173/api/runs/worker/status | Worker 執行狀態 |

---

## 🔧 API 常用端點

```bash
# 設定 base
export CHARTER_BASE="http://172.14.1.140:5173"

# Health Check
curl -fsSL "$CHARTER_BASE/api/health"

# 查看所有腳本
curl -fsSL "$CHARTER_BASE/api/scripts"

# 查看所有 runs
curl -fsSL "$CHARTER_BASE/api/runs"

# 查看 worker 狀態
curl -fsSL "$CHARTER_BASE/api/runs/worker/status"
```

---

## ⚙️ 服務管理

```bash
# SSH 到 Control PC
ssh root@172.14.1.140

# 查看 Charter 服務狀態
systemctl status charter-api charter-web charter-worker

# 重啟服務
systemctl restart charter-api charter-web charter-worker

# 查看 worker log
journalctl -u charter-worker.service -f
```

---

## 📁 目錄結構

| 路徑 | 說明 |
|------|------|
| `/home/da40/charter/apps/web` | Web 程式 |
| `/home/da40/charter/apps/api` | API 程式 |
| `/home/da40/charter/tools` | 工具模組 |
| `/home/da40/charter/data/scripts` | 腳本儲存 |
| `/home/da40/charter/docs_site/site` | 文件站靜態檔 |

---

## 📚 相關文件

| 文件 | 說明 |
|------|------|
| [Tools 工具模組](/tools/) | 工具使用說明 |
| [API Reference](/api_reference/) | API 文件 |
| [Test Suites](/test_suites/sanity/) | 測試腳本列表 |
