# Tools 模組清單（依用途分區）

此頁反映 control PC `172.14.1.140:/home/da40/charter/tools` 目前的實際目錄狀態。


## 1) Runtime（平台/腳本可能會用到）

> 目的：讓客戶/外部單位快速理解「要做某類控制/測試，需要哪些工具」。

### A) Control NOC / Cloud（雲端 API 操作）
用於：login、查 node/location、SSH enable、speedtest、DHCP reservation、reboot…
- `noc_api_cli.py`

### B) Control CPE（對 DUT 的 SSH / 資訊查詢 / Console）
用於：
- 取得裝置狀態（cloud/internet/node-id/password/版本）
- 透過 LAN SSH 執行命令（含 logpull）
- 需要時用 serial/console 協助（依腳本）

工具：
- `cpe_info`
- `cpe_ssh.py`
- `cpe_warehouse_info.py`
- `cpe_console`
- `cpe_console_serial.py`
- `cpe_metrics_agent_serial.py`

### C) Wi‑Fi Client（無線連線測試）
用於：Wi‑Fi sanity/stability（iwd / NetworkManager 連線與斷線）
- `wifi_iwd.py`
- `wifi_nm.py`

### D) LAN Client / DHCP（有線端模擬客戶端）
用於：macvlan 建立 LAN client、DHCP renew、ping 驗證
- `lan_macvlan.py`

### E) UPnP 驗證
用於：UPnP discovery/health 類測試（SSDP/IGD tester）
- `upnp_igd_tester.py`

### F) Serial / Reboot 協助
用於：reboot 期間避免 console/boot loader 被 lock、以及互斥
- `serial_lock.py`
- `serial_mute.py`

### G) Power control（PDU）
用於：power-cycle stability（務必確認 outlet mapping）
- `pdu_outlet1.py`
- `pdu_outlet2.py`

### H) Worker fail-hook / Log 收集
用於：run fail 時自動抓 CPE logpull archive
- `collect_cpe_logs.py`

### I) Run 多 cycle wrapper
用於：把單一 case 以 `CYCLES/INTERVAL/STOP_ON_FAIL` 方式跑 longrun
- `cycle_wrapper.py`

## 2) maint_only（內部維運工具；不建議交付客戶）

- `batch_patch_manifest_zip.py`
- `batch_patch_manifest_zip_text.py`
- `check.cosole.py`
- `modify_script.sh`
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

## 3) _unused_candidate（目前為空；保留作為待移入區）

- （empty）

## 4) Root 其餘工具（未偵測到引用，但仍可能被人工使用）

- `cpe_brwan_capture.py`
- `cpe_capture_role.py`
- `log_rename_add_runid.py`
- `net_probe.py`
- `pbr_cpe.py`
- `run_cpe_metrics_agent.sh`
- `ssh_awlan_tool.py`
- `upnp.status`
