# Sanity Suite — Test Cases（目前平台）



---

## 來源與下載

- GitHub scripts 目錄：<https://github.com/askeywifisit-ui/charter_project/tree/main/scripts/sanity>

- GitHub scripts（sanity 目錄）：<https://github.com/askeywifisit-ui/charter_project/blob/main/scripts/sanity>

### Export script zip（API）

> 說明：`script_id` 可能因 delete/import 變動；建議以 `suite+name` 查到 id 後再 export。

```bash
export CONTROL_PC_IP="172.14.1.140"
export CHARTER_BASE="http://${CONTROL_PC_IP}:5173"
export SUITE="<fill>"
export NAME="sanity"

curl -fsSL "$CHARTER_BASE/api/scripts?limit=2000" -o /tmp/scripts.json

SCRIPT_ID=$(python3 - <<'PY'
import json,os
xs=json.load(open('/tmp/scripts.json'))
name=os.environ.get('NAME')
suite=os.environ.get('SUITE')
ms=[s for s in xs if s.get('suite')==suite and s.get('name')==name]
print(ms[0]['id'] if ms else "")
PY
)

echo "SCRIPT_ID=$SCRIPT_ID"
mkdir -p backup_scripts
curl -fsSL "$CHARTER_BASE/api/scripts/$SCRIPT_ID/export" \
  -o "backup_scripts/${NAME}_${SCRIPT_ID}.zip"
ls -lh "backup_scripts/${NAME}_${SCRIPT_ID}.zip"
```
> 這頁是 **case 目錄**（列出有哪些 sanity scripts），不是教學。
> - 如何跑/看結果：請看 [User Guide → Runs 操作](/user_guide/runs/)
> - 如何匯入/備份/避免 DUPLICATE：請看 [User Guide → Scripts 管理](/user_guide/scripts/)
> - 交付/換環境：請看 [Hand-off（交付外部單位）](/handoff/index/)

> 來源：`GET /api/scripts?suite=sanity`

共 **28** 筆（按名稱排序）：

- C00000001_SSH_basic_test
- C00000002_SSH_disable_test
- C00000003_WIFI_basic_test
- C00000004_NOC_API_basic_test
- C15806902_WLAN_Client_connects_successfully_over_Default_SSID
- C15806905_SSID_broadcast_when_WiFi_radios_toggled
- C15806953_Router_resolves_the_DNS_queries_using_IPv4
- C15807060_WAN_IPv4_Connectivity
- C15807061_WAN_IPv6_Connectivity
- C15807121_Customer_page_should_load_using_Domain_Name_on_LAN_Client
- C15807128_SSH_allowed_local_IP_from_LAN_Client
- C15807129_SSH_allowed_WAN_IP_from_LAN_Client_profile
- C15807130_SSH_allowed_local_IP_from_WLAN_Client
- C15807131_SSH_not_allowed_wrong_credential
- C15807133_SSH_authorized_only_on_port_22
- C15807134_SSH_only_1_session_per_username
- C15807139_SSH_should_be_allowed_to_WAN_from_operator_facing_client
- C15807173_Test_Upnp_discovery
- C15807240_Warehouse_Web_Page_should_load_with_IPv4_address_on_LAN
- C15807241_Warehouse_Web_Page_should_load_with_IPv6_Link_Local_address_on_LAN
- C15807242_Warehouse_Web_Page_should_load_with_Domain_Name
- C15807844_UPnP_State_Changed_From_Disabled_To_Enabled
- C15807850_UPnP_State_Changed_From_Enabled_To_Disabled
- C15807944_Add_DHCP_Reservation
- C15807945_Update_DHCP_Reservation
- C15807946_Delete_DHCP_Reservation
- C15807947_Factory_Reset_DHCP_Reservation
- C15807949_IP_reservation_for_WLAN_connected_clients

## 詳細說明（逐條）
- [C00000001_SSH_basic_test](sanity/C00000001_SSH_basic_test/)
- [C00000002_SSH_disable_test](sanity/C00000002_SSH_disable_test/)
- [C00000003_WIFI_basic_test](sanity/C00000003_WIFI_basic_test/)
- [C00000004_NOC_API_basic_test](sanity/C00000004_NOC_API_basic_test/)
- [C15806902_WLAN_Client_connects_successfully_over_Default_SSID](sanity/C15806902_WLAN_Client_connects_successfully_over_Default_SSID/)
- [C15806905_SSID_broadcast_when_WiFi_radios_toggled](sanity/C15806905_SSID_broadcast_when_WiFi_radios_toggled/)
- [C15806953_Router_resolves_the_DNS_queries_using_IPv4](sanity/C15806953_Router_resolves_the_DNS_queries_using_IPv4/)
- [C15807060_WAN_IPv4_Connectivity](sanity/C15807060_WAN_IPv4_Connectivity/)
- [C15807061_WAN_IPv6_Connectivity](sanity/C15807061_WAN_IPv6_Connectivity/)
- [C15807121_Customer_page_should_load_using_Domain_Name_on_LAN_Client](sanity/C15807121_Customer_page_should_load_using_Domain_Name_on_LAN_Client/)
- [C15807128_SSH_allowed_local_IP_from_LAN_Client](sanity/C15807128_SSH_allowed_local_IP_from_LAN_Client/)
- [C15807129_SSH_allowed_WAN_IP_from_LAN_Client_profile](sanity/C15807129_SSH_allowed_WAN_IP_from_LAN_Client_profile/)
- [C15807130_SSH_allowed_local_IP_from_WLAN_Client](sanity/C15807130_SSH_allowed_local_IP_from_WLAN_Client/)
- [C15807131_SSH_not_allowed_wrong_credential](sanity/C15807131_SSH_not_allowed_wrong_credential/)
- [C15807133_SSH_authorized_only_on_port_22](sanity/C15807133_SSH_authorized_only_on_port_22/)
- [C15807134_SSH_only_1_session_per_username](sanity/C15807134_SSH_only_1_session_per_username/)
- [C15807139_SSH_should_be_allowed_to_WAN_from_operator_facing_client](sanity/C15807139_SSH_should_be_allowed_to_WAN_from_operator_facing_client/)
- [C15807173_Test_Upnp_discovery](sanity/C15807173_Test_Upnp_discovery/)
- [C15807240_Warehouse_Web_Page_should_load_with_IPv4_address_on_LAN](sanity/C15807240_Warehouse_Web_Page_should_load_with_IPv4_address_on_LAN/)
- [C15807241_Warehouse_Web_Page_should_load_with_IPv6_Link_Local_address_on_LAN](sanity/C15807241_Warehouse_Web_Page_should_load_with_IPv6_Link_Local_address_on_LAN/)
- [C15807242_Warehouse_Web_Page_should_load_with_Domain_Name](sanity/C15807242_Warehouse_Web_Page_should_load_with_Domain_Name/)
- [C15807844_UPnP_State_Changed_From_Disabled_To_Enabled](sanity/C15807844_UPnP_State_Changed_From_Disabled_To_Enabled/)
- [C15807850_UPnP_State_Changed_From_Enabled_To_Disabled](sanity/C15807850_UPnP_State_Changed_From_Enabled_To_Disabled/)
- [C15807944_Add_DHCP_Reservation](sanity/C15807944_Add_DHCP_Reservation/)
- [C15807945_Update_DHCP_Reservation](sanity/C15807945_Update_DHCP_Reservation/)
- [C15807946_Delete_DHCP_Reservation](sanity/C15807946_Delete_DHCP_Reservation/)
- [C15807947_Factory_Reset_DHCP_Reservation](sanity/C15807947_Factory_Reset_DHCP_Reservation/)
- [C15807949_IP_reservation_for_WLAN_connected_clients](sanity/C15807949_IP_reservation_for_WLAN_connected_clients/)

> 注意：交付給其他單位時，這份清單會因匯入版本/命名規則而變動；建議交付時附上 scripts export 的 `manifest.json`。

---

## 執行前提醒：sanity cycles 設定

- sanity 類腳本通常用來做「單次冒煙/基本功能驗證」，平台上多數預設 `CYCLES=1`。
- 若你需要：
  - 某一支 sanity script 臨時改成多 cycles（重跑穩定性）
  - 或整個 sanity suite 批次調整 `CYCLES` / `CYCLE_INTERVAL`

  建議用 **OpenClaw 測試助理** 進行「單次 / 批次」修改，避免手動改錯、多檔不一致。

- 詳細操作：請見 [Runbook → Cycles 調整（OpenClaw 測試助理）](/runbook/cycles_edit/)
