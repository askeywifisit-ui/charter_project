# cpe_ssh.py

CPE SSH 控制工具，用於遠端登入 CPE 執行命令。

---

## 位置

`/home/da40/charter/tools/cpe_ssh.py`

---

## 功能

- SSH 登入 CPE
- 執行命令（node-id, reboot, pull-log 等）
- 拉取 CPE Log
- 支援多種指令

---

## 常用範例

### 查詢 CPE 狀態
```bash
# 取得 node-id（用於 NOC API）
python3 /home/da40/charter/tools/cpe_ssh.py --host 192.168.1.1 --cmd node-id

# 取得 WAN IP
python3 /home/da40/charter/tools/cpe_ssh.py --host 192.168.1.1 --cmd wan-ipv4

# 查詢運行時間
python3 /home/da40/charter/tools/cpe_ssh.py --host 192.168.1.1 --cmd uptime
```

### Reboot / Reset
```bash
# Reboot CPE
python3 /home/da40/charter/tools/cpe_ssh.py --host 192.168.1.1 --cmd reboot
```

### 拉取 Log
```bash
# 拉取 CPE Log
python3 /home/da40/charter/tools/cpe_ssh.py --host 192.168.1.1 --cmd pull-log

# 拉取 UPnP Log
python3 /home/da40/charter/tools/cpe_ssh.py --host 192.168.1.1 --cmd upnp-log
```

### 查詢網路狀態
```bash
# DHCP 保留 IP
python3 /home/da40/charter/tools/cpe_ssh.py --host 192.168.1.1 --cmd dhcp-reserved

# DHCP 租約
python3 /home/da40/charter/tools/cpe_ssh.py --host 192.168.1.1 --cmd dhcp-leased

# Wi-Fi 狀態
python3 /home/da40/charter/tools/cpe_ssh.py --host 192.168.1.1 --cmd wifi-vif-state
python3 /home/da40/charter/tools/cpe_ssh.py --host 192.168.1.1 --cmd wifi-radio-state
```

### 支援的指令列表

| 指令 | 功能 |
|------|------|
| `node-id` | 取得 node-id |
| `wan-ipv4` | WAN IPv4 位址 |
| `wan-ipv6` | WAN IPv6 位址 |
| `uptime` | 運行時間 |
| `reboot` | 重啟 CPE |
| `pull-log` | 拉取 Log |
| `upnp-log` | UPnP Log |
| `health` | 健康狀態 |
| `wifi-creds` | Wi-Fi 認證資訊 |
| `dhcp-reserved` | DHCP 保留 IP |
| `dhcp-leased` | DHCP 租約 |
| `wifi-vif-state` | Wi-Fi VIF 狀態 |
| `wifi-radio-state` | Wi-Fi Radio 狀態 |
| `dns-v4` | DNS 查詢 |

---

## 腳本調用範例

```python
import subprocess

result = subprocess.run(
    ['python3', '/home/da40/charter/tools/cpe_ssh.py', 
     '--host', '192.168.1.1', 
     '--cmd', 'node-id'],
    capture_output=True, text=True
)
print(result.stdout)
```
