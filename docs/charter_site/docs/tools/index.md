# Tools（工具模組）

本章整理 Charter 平台使用的工具，位於 `/home/da40/charter/tools`。

> 說明順序：功能 → CLI 用法 → 腳本如何調用 → OpenClaw 如何修改

---

## 🔴 核心工具（必看）

### 1. noc_api_cli.py — NOC API 查詢

**功能**：透過 NOC API 查詢 node/location/upnp/dhcp reservation/WiFi 狀態等

**CLI 用法**：
```bash
cd /home/da40/charter/tools
python3 noc_api_cli.py --help

# 範例：查詢 DHCP reservation
python3 noc_api_cli.py dhcp-reservation-list --profile <profile_name>

# 範例：查詢 UPnP 狀態
python3 noc_api_cli.py upnp-list --profile <profile_name>
```

**腳本調用方式**：
```python
# 在腳本中直接 import
import sys
sys.path.insert(0, '/home/da40/charter/tools')
from noc_api_cli import *

# 或透過 subprocess
import subprocess
result = subprocess.run(
    ['python3', '/home/da40/charter/tools/noc_api_cli.py', 'upnp-list', '--profile', 'default'],
    capture_output=True, text=True
)
```

**OpenClaw 如何修改**：可用 `edit` 工具直接修改 `/home/da40/charter/tools/noc_api_cli.py`

---

### 2. cpe_ssh.py — CPE SSH 控制

**功能**：SSH 登入 CPE、enable/disable、pull log、執行命令

**CLI 用法**：
```bash
python3 /home/da40/charter/tools/cpe_ssh.py --help

# 範例：SSH 登入並執行命令
python3 cpe_ssh.py --cmd "show version"

# 範例：拉 log
python3 cpe_ssh.py --logpull
```

**腳本調用方式**：
```python
import subprocess
result = subprocess.run(
    ['python3', '/home/da40/charter/tools/cpe_ssh.py', '--cmd', 'show version'],
    capture_output=True, text=True
)
```

**OpenClaw 如何修改**：可用 `edit` 工具直接修改 `/home/da40/charter/tools/cpe_ssh.py`

---

### 3. serial_mute.py / serial_lock.py — Serial 控制

**功能**：CPE Serial 控制（mute 靜音、lock 獨占）

**CLI 用法**：
```bash
# Mute（靜音，避免 boot 過程干擾）
python3 /home/da40/charter/tools/serial_mute.py --duration 120

# Lock（獨占 Serial，確保只有一個腳本使用）
python3 /home/da40/charter/tools/serial_lock.py --acquire
python3 /home/da40/charter/tools/serial_lock.py --release
```

**腳本調用方式**：
```python
import subprocess
# mute 120 秒
subprocess.run(['python3', '/home/da40/charter/tools/serial_mute.py', '--duration', '120'])
# lock
subprocess.run(['python3', '/home/da40/charter/tools/serial_lock.py', '--acquire'])
```

**OpenClaw 如何修改**：可用 `edit` 工具修改 `/home/da40/charter/tools/serial_mute.py` 或 `serial_lock.py`

---

### 4. wifi_iwd.py — WiFi 管理（iwd）

**功能**：WiFi 連線/斷線、scan、連線狀態（使用 iwd）

**CLI 用法**：
```bash
python3 /home/da40/charter/tools/wifi_iwd.py --help

# 範例：連線
python3 wifi_iwd.py connect --ssid <SSID> --password <PASSWORD>

# 範例：斷線
python3 wifi_iwd.py disconnect

# 範例：Scan
python3 wifi_iwd.py scan
```

**腳本調用方式**：
```python
import subprocess
subprocess.run(['python3', '/home/da40/charter/tools/wifi_iwd.py', 'connect', '--ssid', 'TestSSID', '--password', 'TestPass'])
```

**OpenClaw 如何修改**：可用 `edit` 工具修改 `/home/da40/charter/tools/wifi_iwd.py`

---

### 5. wifi_nm.py — WiFi 管理（NetworkManager）

**功能**：WiFi 連線/斷線（使用 NetworkManager）

**CLI 用法**：
```bash
python3 /home/da40/charter/tools/wifi_nm.py --help

# 範例：連線
python3 wifi_nm.py connect --ssid <SSID> --password <PASSWORD>
```

**腳本調用方式**：同 wifi_iwd.py，替換指令即可

**OpenClaw 如何修改**：可用 `edit` 工具修改 `/home/da40/charter/tools/wifi_nm.py`

---

### 6. pdu_outlet1.py / pdu_outlet2.py — PDU 控制

**功能**：控制 PDU 插座開關（MSNSwitch/UIS / DLI Web Power Switch）

**CLI 用法**：
```bash
# PDU 1 (MSNSwitch)
python3 /home/da40/charter/tools/pdu_outlet1.py --help

# PDU 2 (DLI)
python3 /home/da40/charter/tools/pdu_outlet2.py --help

# 範例：開啟插座
python3 pdu_outlet1.py on --outlet 1

# 範例：關閉插座
python3 pdu_outlet1.py off --outlet 1
```

**腳本調用方式**：
```python
subprocess.run(['python3', '/home/da40/charter/tools/pdu_outlet1.py', 'on', '--outlet', '1'])
```

**OpenClaw 如何修改**：可用 `edit` 工具修改 `/home/da40/charter/tools/pdu_outlet1.py` 或 `pdu_outlet2.py`

---

### 7. cpe_info — CPE 資訊

**功能**：快速查看 DUT（CPE）狀態、版本、IP 等

**CLI 用法**：
```bash
/home/da40/charter/tools/cpe_info --status
/home/da40/charter/tools/cpe_info --version
```

**腳本調用方式**：
```python
subprocess.run(['/home/da40/charter/tools/cpe_info', '--status'])
```

**OpenClaw 如何修改**：可用 `edit` 工具修改 `/home/da40/charter/tools/cpe_info`

---

### 8. cycle_wrapper.py — 腳本包裝

**功能**：腳本入口包裝，載入 manifest.yaml 環境變數

**CLI 用法**：
```bash
# 腳本的 entrypoint 通常是 cycle_wrapper.py:run
python3 /home/da40/charter/tools/cycle_wrapper.py --help
```

**腳本調用方式**：腳本 ZIP 的 `manifest.yaml` 中指定 `entrypoint: cycle_wrapper.py:run`

**OpenClaw 如何修改**：可用 `edit` 工具修改 `/home/da40/charter/tools/cycle_wrapper.py`

---

## 🟡 網路工具

### lan_macvlan.py

**功能**：建立 MACVLAN 介面

**CLI 用法**：
```bash
python3 /home/da40/charter/tools/lan_macvlan.py --help
```

**OpenClaw 如何修改**：可用 `edit` 工具修改

---

### net_probe.py

**功能**：網路探測（ping/tcpdump/dig）

**CLI 用法**：
```bash
python3 /home/da40/charter/tools/net_probe.py --help
```

**OpenClaw 如何修改**：可用 `edit` 工具修改

---

## 🟢 其他工具（查閱）

- [collect_cpe_logs.py](collect_cpe_logs.md) — CPE Log 收集
- [cpe_console](cpe_console.md) — Console 存取
- [log_rename_add_runid.py](log_rename_add_runid.md) — Log 重新命名
- [upnp_igd_tester.py](upnp_igd_tester.md) — UPnP 測試

---

## ⚫ 閒置工具（勿用）

以下工具已移至 `_unused_candidate/`，請勿使用：

- `ssh_awlan_tool.py`（舊版）
- `upnp.status`
- `cpe_brwan_capture.py`
- `cpe_capture_role.py`
- `cpe_warehouse_info.py`
- `collect_cpe_logs.py`
- `log_rename_add_runid.py`
- `pbr_cpe.py`
- `run_cpe_metrics_agent.sh`
- `upnp_igd_tester.py`

---

## OpenClaw 如何管理工具

1. **查看工具列表**：`ssh root@172.14.1.140 "ls -la /home/da40/charter/tools/"`
2. **修改工具**：用 `edit` 工具直接修改 `/home/da40/charter/tools/<tool_name>.py`
3. **測試工具**：在腳本中先用 `subprocess.run(['python3', '/home/da40/charter/tools/<tool>.py', ...])` 測試
4. **部署**：修改後需同步到其他 Charter 節點（如 11F_131）
