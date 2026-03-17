# 交付環境表（對方要填）

> 建議交付時請對方把這張表填完並回傳，避免「網卡/路徑/網段」不一致造成大量來回。
>
> **參數放置建議（移植到新平台時最省事）**
> - **平台固定（跟著 control PC/server 走）**：放在 `charter-worker.service`（systemd `Environment=`）
>   - 例如：`WIFI_IFACE` / `LAN_PARENT_IFACE` / `PING_IFACE` / `CPE_DEV` / `PDU_SCRIPT` / `PDU_OUTLET_ID` / `TEST_PROFILE`
> - **DUT 變動（換 CPE/DUT 才會變）**：放在 `/home/da40/charter/.secrets/dut.env`（systemd `EnvironmentFile=`）或維持在各 script 的 `manifest.yaml`
>   - 例如：`CUSTOMER_ID` / `NOC_PROFILE` / `SSH_HOST_LAN`
>
> 

**DHCP Reservation 建議（避免腳本 flakiness）**
- 建議預留 DHCP reservation 區段，例如 `192.168.1.240~249`，讓 reservation 測試不會跟一般 DHCP lease 撞 IP。
- 相關腳本（例如 `C15807949`）建議預設 `TEST_RESERVED_IP=192.168.1.240`，必要時搭配 `AUTO_PICK_FREE_IP=1`。
**優先序規則（避免跑錯介面名）**
> - 建議以「平台環境」為準，`manifest.yaml` 只提供 *defaults*（不要把 `wlx.../eno2` 之類寫死在 manifest）。
> - 換句話說：**manifest 沒寫 → 吃環境變數；manifest 寫了也不要覆蓋平台環境**（除非你明確要做特殊覆蓋）。

## 1) Control PC / 平台
- Control PC IP：`{{CONTROL_PC_IP}}`
- UI Base：`http://{{CONTROL_PC_IP}}:5173`
- API Base：`http://{{CONTROL_PC_IP}}:5173/api`

## 2) Control PC 路徑（如需調整）
- tools：`{{TOOLS_DIR}}`（例：`/home/da40/charter/tools`）
- web：`{{WEB_DIR}}`（例：`/home/da40/charter/apps/web`）
- api：`{{API_DIR}}`（例：`/home/da40/charter/apps/api/app/`）
- data：`{{DATA_DIR}}`（例：`/home/da40/charter/data`）

## 3) 網卡 / 網路（最常踩雷）

### 常見額外欄位
- 測試情境/環境標籤：`{{TEST_PROFILE}}`
  - 例：`customer`
- cycles 間隔（某些 stability/sanity 會用）：`{{CYCLE_INTERVAL}}`
  - 例：`60`

> 請貼上以下命令輸出：
```bash
ip link
ip route
```

- LAN parent iface（給 lan_macvlan 用）：`{{LAN_PARENT_IFACE}}`
- Wi‑Fi iface（給 wifi_iwd/wifi_nm 用）：`{{WIFI_IFACE}}`
- Ping iface（可選）：`{{PING_IFACE}}`

## 4) CPE / DUT
- CPE LAN IP：`{{CPE_HOST}}`（例：`192.168.1.1`）
- SSH user：`{{CPE_SSH_USER}}`（例：`operator`）
- SSH port：`{{CPE_SSH_PORT}}`（例：`22`）

### （客戶環境常見額外欄位）
- Serial device（console board）：`{{CPE_DEV}}`
  - 例：`/dev/serial/by-id/usb-ASKEY_ASKEY_Console_Board_FT4PGJN6-if02-port0`
- CPE WAN gateway（若腳本需要指定 WAN 預設閘道）：`{{CPE_WAN_GATEWAY}}`
  - 例：`211.72.175.254`

## 5) NOC / Cloud
- profiles 檔案：`{{PROFILES_FILE}}`（例：`/home/da40/charter/.secrets/noc_profiles.json`）
- profile 名稱：`{{NOC_PROFILE}}`（例：`SPECTRUM_INT`）
- customer_id：`{{CUSTOMER_ID}}`

## 6) PDU（如有 power-cycle 類 stability）
- PDU script：`{{PDU_SCRIPT}}`（例：`/home/da40/charter/tools/pdu_outlet1.py`）
- PDU outlet id（若工具/腳本有用到）：`{{PDU_OUTLET_ID}}`
  - 例：`1`
- outlet mapping（哪個 outlet 對應哪台 DUT）：
  - outlet1 → __________
  - outlet2 → __________

> 若對方環境沒有 PDU，請明確註記：哪些 stability case 不可執行。
