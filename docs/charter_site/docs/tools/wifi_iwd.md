# wifi_iwd.py

WiFi 控制工具（使用 iwd/iwctl）。

---

## 位置

`/home/da40/charter/tools/wifi_iwd.py`

---

## 功能

- WiFi 連線/斷線
- Scan 周邊網路
- 支援 PBR（Policy-Based Routing）

---

## 常用範例

### 連線到 WiFi
```bash
# 連線到 SSID
python3 /home/da40/charter/tools/wifi_iwd.py ensure \
  --iface wlan0 \
  --ssid TestNetwork \
  --password TestPass123
```

### 斷線
```bash
# 斷開 WiFi
python3 /home/da40/charter/tools/wifi_iwd.py disconnect --iface wlan0
```

### Scan 周邊網路
```bash
#  Scan 可用網路
python3 /home/da40/charter/tools/wifi_iwd.py scan --iface wlan0
```

### 查詢狀態
```bash
# 查詢連線狀態
python3 /home/da40/charter/tools/wifi_iwd.py status --iface wlan0
```

### 進階選項
```bash
# 指定頻段（5G）
python3 /home/da40/charter/tools/wifi_iwd.py ensure \
  --iface wlan0 \
  --ssid TestNetwork \
  --password TestPass123 \
  --band 5g

# 使用 DHCP timeout
python3 /home/da40/charter/tools/wifi_iwd.py ensure \
  --iface wlan0 \
  --ssid TestNetwork \
  --password TestPass123 \
  --dhcp-timeout 30
```

---

## 參數說明

| 參數 | 說明 |
|------|------|
| `--iface` | WiFi 介面名稱（如 wlan0, wlx...） |
| `--ssid` | 網路名稱 |
| `--password` | WiFi 密碼 |
| `--band` | 頻段（2g, 5g, 6g） |
| `--timeout` | 連線逾時 |
| `--dhcp-timeout` | DHCP 逾時 |

---

## 腳本調用範例

```python
import subprocess

# 連線到 WiFi
subprocess.run([
    'python3', '/home/da40/charter/tools/wifi_iwd.py', 'ensure',
    '--iface', 'wlan0',
    '--ssid', 'TestSSID',
    '--password', 'TestPass'
])

# Scan
result = subprocess.run([
    'python3', '/home/da40/charter/tools/wifi_iwd.py', 'scan',
    '--iface', 'wlan0'
], capture_output=True, text=True)
print(result.stdout)
```
