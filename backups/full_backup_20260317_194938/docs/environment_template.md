# Environment Template（環境參數範本）

本頁說明 Charter 平台移植到新環境時，需要設定哪些參數。

---

## 參數要填到哪裡？

| 類型 | 位置 | 說明 |
|------|------|------|
| 平台固定參數 | **systemd** (`charter-worker.service`) | LAN/WIFI 網卡、Serial、PDU 等 |
| 敏感資訊 | **`.secrets/dut.env`** | SSH 密碼、Warehouse 密碼等 |
| NOC 帳號 | **`.secrets/noc_profiles.json`** | NOC email / password |
| 腳本參數 | **manifest.yaml** | 每個腳本不同（timeout、IP 等） |

---

## 1️⃣ systemd 參數（平台固定）

在 `/etc/systemd/system/charter-worker.service.d/override.conf` 設定：

```bash
[Service]
Environment=WIFI_IFACE=wlx6cb0ce1ff230
Environment=LAN_PARENT_IFACE=eno2
Environment=PING_IFACE=eno2
Environment=CPE_DEV=/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_B0008Z1P-if00-port0
Environment=PDU_SCRIPT=/home/da40/charter/tools/pdu_outlet1.py
Environment=PDU_OUTLET_ID=1
Environment=TEST_PROFILE=lab
EnvironmentFile=-/home/da40/charter/.secrets/dut.env
```

### 參數說明

| 參數 | 說明 | 範例 |
|------|------|------|
| `WIFI_IFACE` | Wi-Fi 測試介面 | `wlan0`, `wlx6cb0ce1ff230` |
| `LAN_PARENT_IFACE` | LAN client 模擬介面 | `eno2`, `enx245ebe6507f7` |
| `PING_IFACE` | ping 走哪張卡 | `eno2` |
| `CPE_DEV` | Serial port（stable path） | `/dev/serial/by-id/...` |
| `PDU_SCRIPT` | PDU 控制腳本 | `pdu_outlet1.py` |
| `PDU_OUTLET_ID` | 插座編號 | `1` |
| `TEST_PROFILE` | 測試設定檔名 | `lab` |

### 查詢網卡

```bash
# 列出所有網卡
ip -o link show | sed -E 's/^[0-9]+: /- /'

# 查 LAN iface（看 192.168.1.0/24 走哪張卡）
ip -o route show | egrep '192\.168\.1\.'
```

### 查詢 Serial Port

```bash
ls -la /dev/serial/by-id/
```

---

## 2️⃣ 敏感資訊（dut.env）

建立 `/home/da40/charter/.secrets/dut.env`（權限 600）：

```bash
WAREHOUSE_ID=ThylacineGone
WAREHOUSE_PASSWORD=<fill>
SSH_PASSWORD=<fill>
```

---

## 3️⃣ NOC 帳號（noc_profiles.json）

建立 `/home/da40/charter/.secrets/noc_profiles.json`：

```json
{
  "SPECTRUM_INT": {
    "base": "https://piranha-int.tau.dev-charter.net",
    "email": "<fill>",
    "password": "<fill>"
  }
}
```

腳本只需要指定：
- `PROFILES_FILE=/home/da40/charter/.secrets/noc_profiles.json`
- `NOC_PROFILE=SPECTRUM_INT`
- `CUSTOMER_ID=<fill>`

---

## 4️⃣ 腳本參數（manifest.yaml）

每個腳本的 `manifest.yaml` 中可設定：

| 參數 | 說明 |
|------|------|
| `TOOLS_PATH` | 工具路徑 |
| `CPE_HOST` | CPE LAN IP（預設 `192.168.1.1`） |
| `CUSTOMER_ID` | 客戶 ID |
| `CYCLES` | 迴圈次數 |
| `STOP_ON_FAIL` | 失敗停止（true/false） |
| `TIMEOUT` |逾時秒數 |

> 敏感資訊（密碼）不要寫在 manifest，放到 `dut.env` 或 `noc_profiles.json`。

---

## 📋 11F_140 參考值

| 參數 | 值 |
|------|-----|
| CONTROL_PC_IP | 172.14.1.140 |
| WIFI_IFACE | wlx6cb0ce1ff230 |
| LAN_PARENT_IFACE | eno2 |
| PING_IFACE | eno2 |
| CPE_DEV | /dev/serial/by-id/usb-FTDI_FT232R_USB_UART_B0008Z1P-if00-port0 |
| PDU_IP | 172.14.1.135 |
| PDU_SCRIPT | pdu_outlet1.py |
| PDU_OUTLET_ID | 1 |

---

## 🔗 相關文件

- [Platform Links](/platform_links/) — 常用入口
- [Tools 工具模組](/tools/) — 工具使用說明
- [PDU 控制](/tools/pdu/) — PDU 詳細說明
