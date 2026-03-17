# Tools（工具模組）

Charter 平台工具位於 `/home/da40/charter/tools`。

---

## 下載工具

- [GitHub - charter_project/tools](https://github.com/askeywifisit-ui/charter_project/tree/main/charter_project/tools)

---

## 工具目錄

| 工具 | 功能 | 路徑 |
|------|------|------|
| **noc_api_cli.py** | NOC API 查詢 | `/home/da40/charter/tools/noc_api_cli.py` |
| **cpe_ssh.py** | CPE SSH 控制 | `/home/da40/charter/tools/cpe_ssh.py` |
| **serial_mute.py** | Serial 靜音 | `/home/da40/charter/tools/serial_mute.py` |
| **serial_lock.py** | Serial 獨占 | `/home/da40/charter/tools/serial_lock.py` |
| **wifi_iwd.py** | WiFi 管理（iwd） | `/home/da40/charter/tools/wifi_iwd.py` |
| **wifi_nm.py** | WiFi 管理（NM） | `/home/da40/charter/tools/wifi_nm.py` |
| **pdu_outlet1.py** | PDU 控制（MSNSwitch） | `/home/da40/charter/tools/pdu_outlet1.py` |
| **pdu_outlet2.py** | PDU 控制（DLI） | `/home/da40/charter/tools/pdu_outlet2.py` |
| **cpe_info** | CPE 資訊查詢 | `/home/da40/charter/tools/cpe_info` |
| **lan_macvlan.py** | MACVLAN 介面 | `/home/da40/charter/tools/lan_macvlan.py` |
| **net_probe.py** | 網路探測 | `/home/da40/charter/tools/net_probe.py` |
| **collect_cpe_logs.py** | CPE Log 收集 | `/home/da40/charter/tools/collect_cpe_logs.py` |
| **cpe_console** | Console 存取 | `/home/da40/charter/tools/cpe_console` |
| **cpe_console_serial.py** | Serial Console | `/home/da40/charter/tools/cpe_console_serial.py` |
| **cpe_metrics_agent_serial.py** | Metrics Agent | `/home/da40/charter/tools/cpe_metrics_agent_serial.py` |
| **cpe_warehouse_info.py** | Warehouse 資訊 | `/home/da40/charter/tools/cpe_warehouse_info.py` |
| **pbr_cpe.py** | PBR 控制 | `/home/da40/charter/tools/pbr_cpe.py` |
| **ssh_awlan_tool.py** | SSH AWLAN 工具 | `/home/da40/charter/tools/ssh_awlan_tool.py` |
| **upnp_igd_tester.py** | UPnP 測試 | `/home/da40/charter/tools/upnp_igd_tester.py` |

---

## 常用指令速查

### CPE 狀態查詢
```bash
/home/da40/charter/tools/cpe_info --status
```

### NOC API
```bash
cd /home/da40/charter/tools
python3 noc_api_cli.py dhcp-reservation-list --profile <PROFILE>
python3 noc_api_cli.py upnp-list --profile <PROFILE>
```

### SSH 控制
```bash
python3 /home/da40/charter/tools/cpe_ssh.py --cmd "show version"
python3 /home/da40/charter/tools/cpe_ssh.py --logpull
```

### Serial 控制
```bash
python3 /home/da40/charter/tools/serial_mute.py --duration 120
python3 /home/da40/charter/tools/serial_lock.py --acquire
python3 /home/da40/charter/tools/serial_lock.py --release
```

### WiFi 控制（iwd）
```bash
python3 /home/da40/charter/tools/wifi_iwd.py connect --ssid <SSID> --password <PASS>
python3 /home/da40/charter/tools/wifi_iwd.py disconnect
python3 /home/da40/charter/tools/wifi_iwd.py scan
```

### PDU 控制
```bash
python3 /home/da40/charter/tools/pdu_outlet1.py on --outlet 1
python3 /home/da40/charter/tools/pdu_outlet1.py off --outlet 1
```

---

## 腳本調用範例

```python
import subprocess

# NOC API
result = subprocess.run(
    ['python3', '/home/da40/charter/tools/noc_api_cli.py', 'upnp-list', '--profile', 'default'],
    capture_output=True, text=True
)

# CPE SSH
result = subprocess.run(
    ['python3', '/home/da40/charter/tools/cpe_ssh.py', '--cmd', 'show version'],
    capture_output=True, text=True
)

# WiFi
subprocess.run(['python3', '/home/da40/charter/tools/wifi_iwd.py', 'connect', 
                '--ssid', 'TestSSID', '--password', 'TestPass'])

# PDU
subprocess.run(['python3', '/home/da40/charter/tools/pdu_outlet1.py', 'on', '--outlet', '1'])
```

---

## OpenClaw 管理

| 動作 | 指令 |
|------|------|
| 查看工具列表 | `ssh root@172.14.1.140 "ls -la /home/da40/charter/tools/"` |
| 修改工具 | 用 `edit` 工具直接修改 `/home/da40/charter/tools/<tool>.py` |
| 部署到其他節點 | 同步到 11F_131 等 |
