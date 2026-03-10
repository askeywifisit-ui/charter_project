# Tools（常用工具模組 / 同事速查）

本章整理 control PC 上的 tools：`/home/da40/charter/tools`。

> 原則：工具文件只放「用法」，不放任何 NOC email/password / SSH 密碼等敏感值。

---

## 先看這三個（最常用）

1) `cpe_info`：快速看 DUT 狀態/版本
- 文件：[cpe_info](cpe_info.md)

2) `cpe_ssh.py`：SSH enable/disable/check + 拉 log
- 文件：[cpe_ssh.py](cpe_ssh.md)

3) `noc_api_cli.py`：用 NOC API 查 node/location/upnp/dhcp reservation 等
- 文件：[noc_api_cli.py](noc_api_cli.md)

---

## 同事常用指令（不查文件也能直接跑）

```bash
# 1) API/worker quick check
export CHARTER_BASE="http://<CONTROL_PC_IP>:5173"
curl -fsSL "$CHARTER_BASE/api/health" | python3 -m json.tool
curl -fsSL "$CHARTER_BASE/api/runs/worker/status" | python3 -m json.tool

# 2) CPE status
/home/da40/charter/tools/cpe_info --status || true

# 3) SSH enable/disable
python3 /home/da40/charter/tools/cpe_ssh.py --help | head

# 4) NOC (需要 .secrets 注入 NOC profile)
python3 /home/da40/charter/tools/noc_api_cli.py --help | head
```

---

## 常用工具（文件入口）

- [cpe_info](cpe_info.md)
- [cpe_ssh.py](cpe_ssh.md)
- [noc_api_cli.py](noc_api_cli.md)
- [wifi_iwd.py](wifi_iwd.md)
- [wifi_nm.py](wifi_nm.md)
- [lan_macvlan.py](lan_macvlan.md)
- [serial_mute.py](serial_mute.md)
- [serial_lock.py](serial_lock.md)
- [pdu_outlet1.py / pdu_outlet2.py](pdu.md)
- [collect_cpe_logs.py](collect_cpe_logs.md)

---

## Tools 全清單（供查找檔名）

<!-- TOOL_LIST_START -->
```text
batch_patch_manifest_zip.py
batch_patch_manifest_zip_text.py
check.cosole.py
collect_cpe_logs.py
cpe_brwan_capture.py
cpe_capture_role.py
cpe_console
cpe_console_serial.py
cpe_info
cpe_metrics_agent_serial.py
cpe_ssh.py
cpe_warehouse_info.py
cycle_wrapper.py
lan_macvlan.py
log_rename_add_runid.py
modify_script.sh
net_probe.py
noc_api_cli.py
pbr_cpe.py
pbr_cpe_sshpass.py
pbr_watchdog.sh
pbr_watchdog_event.sh
pdu_outlet1.py
pdu_outlet2.py
run_cpe_metrics_agent.sh
serial_lock.py
serial_mute.py
ssh_awlan_tool.py
test_upnp_cli.sh
upnp.status
upnp_igd_tester.py
upnp_igd_tester_capture.py
verify_dhcp_resv_api.py
verify_lan_macvlan.py
verify_upnp_realized.sh
verify_wifi_nm.sh
wifi_connect_disconnect_check.sh
wifi_iwd.py
wifi_nm.py
wifi_station_count
wifi_station_count_serial.py
```
<!-- TOOL_LIST_END -->
