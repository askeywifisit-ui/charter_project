# noc_api_cli.py

NOC API 命令列工具，用於操作 Charter NOC/Cloud 平台。

---

## 位置

`/home/da40/charter/tools/noc_api_cli.py`

---

## 功能

- 查詢與控制 CPE 節點
- DHCP Reservation 管理
- Wi-Fi 開關/設定
- UPnP 開關/設定
- LTE 開關
- Speedtest 執行與查詢
- Reboot / Factory Reset
- SSH 開關

---

## 環境設定

```bash
# 從 secrets 讀取設定
export PROFILES_FILE=/home/da40/charter/.secrets/noc_profiles.json
export NOC_PROFILE=SPECTRUM_INT
export CUSTOMER_ID=<your_customer_id>
```

---

## 常用指令

### 登入取得 Token
```bash
python3 /home/da40/charter/tools/noc_api_cli.py login
```

### 查詢節點
```bash
# 從 node-id 取得 location-id
python3 /home/da40/charter/tools/noc_api_cli.py get-location --node-id <NODE_ID>

# 查詢節點狀態
python3 /home/da40/charter/tools/noc_api_cli.py node-status --location-id <LOCATION_ID>
```

### SSH 控制
```bash
# 啟用 SSH
python3 /home/da40/charter/tools/noc_api_cli.py ssh-enable

# 關閉 SSH
python3 /home/da40/charter/tools/noc_api_cli.py ssh-disable
```

### Wi-Fi 控制
```bash
# 查詢 Wi-Fi 狀態
python3 /home/da40/charter/tools/noc_api_cli.py wifi-status

# 啟用 Wi-Fi
python3 /home/da40/charter/tools/noc_api_cli.py wifi-enable

# 關閉 Wi-Fi
python3 /home/da40/charter/tools/noc_api_cli.py wifi-disable

# 設定 SSID/密碼
python3 /home/da40/charter/tools/noc_api_cli.py wifi-config-set --ssid <SSID> --psk <PASSWORD>
```

### UPnP 控制
```bash
# 查詢 UPnP 狀態
python3 /home/da40/charter/tools/noc_api_cli.py upnp-status

# 啟用 UPnP
python3 /home/da40/charter/tools/noc_api_cli.py upnp-enable

# 關閉 UPnP
python3 /home/da40/charter/tools/noc_api_cli.py upnp-disable
```

### LTE 控制
```bash
# 查詢 LTE 狀態
python3 /home/da40/charter/tools/noc_api_cli.py lte-status

# 啟用 LTE
python3 /home/da40/charter/tools/noc_api_cli.py lte-enable

# 關閉 LTE
python3 /home/da40/charter/tools/noc_api_cli.py lte-disable
```

### DHCP Reservation
```bash
# 列出所有 Reservation
python3 /home/da40/charter/tools/noc_api_cli.py dhcp-resv-list

# 查詢單一 Reservation
python3 /home/da40/charter/tools/noc_api_cli.py dhcp-resv-get --mac <MAC_ADDRESS>

# 新增/修改 Reservation
python3 /home/da40/charter/tools/noc_api_cli.py dhcp-resv-set --mac <MAC> --ip <IP>

# 刪除 Reservation
python3 /home/da40/charter/tools/noc_api_cli.py dhcp-resv-del --mac <MAC_ADDRESS>
```

### Speedtest
```bash
# 觸發 Speedtest
python3 /home/da40/charter/tools/noc_api_cli.py speedtest-run

# 查詢所有結果
python3 /home/da40/charter/tools/noc_api_cli.py speedtest-results

# 查詢特定結果
python3 /home/da40/charter/tools/noc_api_cli.py speedtest-result --request-id <REQUEST_ID>
```

### Reboot / Reset
```bash
# Reboot
python3 /home/da40/charter/tools/noc_api_cli.py reboot

# Factory Reset
python3 /home/da40/charter/tools/noc_api_cli.py factory-reset
```

---

## 腳本調用範例

```python
import subprocess

# 查詢 Wi-Fi 狀態
result = subprocess.run(
    ['python3', '/home/da40/charter/tools/noc_api_cli.py', 'wifi-status'],
    capture_output=True, text=True
)

# 啟用 SSH
result = subprocess.run(
    ['python3', '/home/da40/charter/tools/noc_api_cli.py', 'ssh-enable'],
    capture_output=True, text=True
)

# DHCP Reservation
result = subprocess.run(
    ['python3', '/home/da40/charter/tools/noc_api_cli.py', 'dhcp-resv-list'],
    capture_output=True, text=True
)
```

---

## 常見錯誤

### `noc-context timeout`
- 原因：NOC endpoint 慢、網路問題
- 解決：retry、拉長 timeout

### `Unauthorized`
- 原因：Token 過期或帳密錯誤
- 解決：重新 login
