# Tools（常用工具模組）

本章整理 `172.14.1.140` control PC 上的 tools：`/home/da40/charter/tools`。

## 清單來源與篩選規則
- 來源：`ls -1 /home/da40/charter/tools`
- **不列入備份檔**：檔名含 `.bak` 或 `.bak.<timestamp>`
- 不列入：`old/`、`__pycache__/`
- 不列入（內部整理用目錄）：`maint_only/`、`_unused_candidate/`

> 交付其他單位時，請先看：Environment Template（路徑/網卡/NOC profile 需替換）。

## 常用工具（優先補 CLI 用法）
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

## Tools 全清單（已過濾 .bak/old/__pycache__）

更新方式（會從 control PC 抓最新清單並覆寫本段）：
```bash
python3 scripts/update_charter_tools_index.py --host 172.14.1.140 --user root
```

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
