# wifi_nm.py

WiFi 控制工具（使用 NetworkManager/nmcli）。

---

## 位置

`/home/da40/charter/tools/wifi_nm.py`

---

## 功能

- WiFi 連線/斷線（使用 nmcli）
- Scan 周邊網路
- 查詢連線狀態

---

## 常用指令

### 基本語法
```bash
python3 /home/da40/charter/tools/wifi_nm.py <COMMAND> --iface <INTERFACE>
```

### 指令

```bash
# 查詢狀態
python3 /home/da40/charter/tools/wifi_nm.py status --iface wlan0

# Scan
python3 /home/da40/charter/tools/wifi_nm.py scan --iface wlan0

# 連線
python3 /home/da40/charter/tools/wifi_nm.py ensure --iface wlan0 --ssid <SSID> --password <PASSWORD>

# 斷線
python3 /home/da40/charter/tools/wifi_nm.py disconnect --iface wlan0
```

---

## 與 wifi_iwd.py 的差異

| 工具 | 底層 | 適用場景 |
|------|------|----------|
| `wifi_iwd.py` | iwd/iwctl | 測試環境 |
| `wifi_nm.py` | NetworkManager | 一般環境 |

---

## 腳本調用範例

```python
import subprocess

# 連線到 WiFi
subprocess.run([
    'python3', '/home/da40/charter/tools/wifi_nm.py', 'ensure',
    '--iface', 'wlan0',
    '--ssid', 'TestSSID',
    '--password', 'TestPass'
])
```
