# Tools 分類（Runtime vs Maint-only vs 可刪候選）

本頁用來支援「交付外部單位/客戶」時，將 tools 最小化。

**說明**：此分類包含自動掃描推估（scripts + api/web 字串引用）與經驗判斷；刪除前仍需人工確認。


## 1) Runtime 必需（建議保留並可交付）
- 依據：被 scripts/api/web 偵測到引用，或屬於核心執行鏈（cpe_ssh/cpe_info/noc/wifi/lan/serial/pdu/fail-hook）。

- `collect_cpe_logs.py` (core)
- `cpe_console` (core)
- `cpe_console_serial.py` (used, core)
- `cpe_info` (used, core)
- `cpe_metrics_agent_serial.py` (used, core)
- `cpe_ssh.py` (used, core)
- `cpe_warehouse_info.py` (used)
- `cycle_wrapper.py` (core)
- `lan_macvlan.py` (core)
- `noc_api_cli.py` (used, core)
- `pdu_outlet1.py` (used, core)
- `pdu_outlet2.py` (used, core)
- `serial_lock.py` (core)
- `serial_mute.py` (used, core)
- `upnp_igd_tester.py` (used)
- `wifi_iwd.py` (used, core)
- `wifi_nm.py` (used, core)

## 2) Maint-only（內部維運用，建議移到 tools/old/maint_only，不交付客戶）
- 依據：未偵測到平台自動引用，但看起來屬於批次 patch / verify / 診斷 / 監控 / 一次性工具。

- `batch_patch_manifest_zip.py`
- `batch_patch_manifest_zip_text.py`
- `check.cosole.py`
- `log_rename_add_runid.py`
- `modify_script.sh`
- `net_probe.py`
- `pbr_cpe.py`
- `pbr_cpe_sshpass.py`
- `pbr_watchdog.sh`
- `pbr_watchdog_event.sh`
- `test_upnp_cli.sh`
- `upnp_igd_tester_capture.py`
- `verify_dhcp_resv_api.py`
- `verify_lan_macvlan.py`
- `verify_upnp_realized.sh`
- `verify_wifi_nm.sh`
- `wifi_connect_disconnect_check.sh`
- `wifi_station_count`
- `wifi_station_count_serial.py`

## 3) 可刪候選（低價值/未引用；請你最後裁決）
- 依據：未被偵測引用，且不落在常見維運工具型態。

- `artifacts`
- `cpe_brwan_capture.py`
- `cpe_capture_role.py`
- `run_cpe_metrics_agent.sh`
- `ssh_awlan_tool.py`
- `upnp.status`
