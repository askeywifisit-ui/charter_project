## Step 4️⃣：複製 Secrets

> ⚠️ 建議重新設定，不要直接用舊的！

```bash
# NOC 設定
nano /home/da40/charter/.secrets/noc_profiles.json

# DUT 設定
nano /home/da40/charter/.secrets/dut.env
```

> ✅ **修改 noc_profiles.json 後，需執行以下指令讓新設定生效：**
> ```bash
> sudo systemctl restart charter-worker
> ```

---

## Step 5️⃣：複製 CPE Metrics Agent 設定

> ⚠️ 不同機器的 USB Serial 設備和網卡不同，需要修改！

```bash
# 複製並編輯設定檔
sudo cp /etc/default/cpe-metrics-agent /etc/default/cpe-metrics-agent.bak
sudo nano /etc/default/cpe-metrics-agent
```

### 重要參數說明

| 參數 | 說明 | 131 | 140 | 200 |
|------|------|-----|-----|-----|
| CPE_SERIAL | USB Serial 設備 | /dev/ttyUSB0 | (無) | (無) |
| CPE_IFACE | 連接 CPE 的網卡 | eth0 | eth0 | eth0 |
| CPE_BAUD | 鮑率 | 115200 | 115200 | 115200 |
| PBR_IFACE | 主機上連接 CPE 的網卡 | enx00e04c6809c3 | eno2 | enp3s0 |
| CPE_USER | 登入帳號 | root | root | root |

### 自動偵測

如果不指定 `CPE_SERIAL`，腳本會自動偵測：
1. `/dev/serial/by-id/usb-ASKEY_ASKEY_Console_Board_*`
2. `/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_*`
3. Fallback: `/dev/ttyUSB0`

---

---

## Step 6️⃣：複製 Systemd 服務

```bash
cd /home/da40
sudo cp /etc/systemd/system/charter-api.service .
sudo cp -r /etc/systemd/system/charter-api.service.d .
sudo cp /etc/systemd/system/charter-web.service .
sudo cp /etc/systemd/system/charter-worker.service .
sudo cp /etc/systemd/system/cpe-metrics-agent.service .
sudo cp /etc/systemd/system/pbr-watchdog.service .
sudo cp /etc/systemd/system/cpe-status-probe.timer .
sudo cp /etc/systemd/system/cpe-status-probe.service .
```

> ⚠️ `charter-api.service.d/` 包含資料庫連線設定（`10-db.conf`），確認內容正確後再啟動服務。

---

## Step 7️⃣：啟動服務

```bash
sudo systemctl daemon-reload
sudo systemctl enable \
  charter-api \
  charter-web \
  charter-worker \
  cpe-metrics-agent \
  cpe-status-probe.timer \
  pbr-watchdog

sudo systemctl restart \
  charter-api \
  charter-web \
  charter-worker \
  cpe-metrics-agent \
  cpe-status-probe.timer \
  pbr-watchdog
```

---

## ✅ 驗證

```bash
# API Health
curl http://127.0.0.1:8080/api/health
# 預期：{"ok":true}

# Systemd 服務
systemctl status charter-api charter-web charter-worker cpe-metrics-agent cpe-status-probe.timer pbr-watchdog
```

---

## 🔧 服務對照

| 服務 | Port | 用途 |
|:-----|:----:|:-----|
| charter-api | 8080 | API 後端 |
| charter-web | 5173 | Web UI |
| charter-worker | - | 腳本執行器 |
| cpe-metrics-agent | - | CPE 監控 |
| cpe-status-probe | - | CPE 狀態探針 |
| pbr-watchdog | - | PBR 路由維護 |

---

## ❓ 常見問題

| 問題 | 原因 | 解決 |
|------|------|------|
| API 502 | 服務未啟動 | `systemctl restart charter-api` |
| Web UI 空白 | API 未正常 | 檢查 charter-api 健康狀態 |
| CPE 無資料 | Serial 未連接 | 檢查 `/etc/default/cpe-metrics-agent` 中的 `CPE_SERIAL` |

---

## 📌 相關頁面

| 頁面 | 說明 |
|:-----|:-----|
| [🏠 平台安裝](../../getting_started/platform_install/) | 完整安裝流程 |
