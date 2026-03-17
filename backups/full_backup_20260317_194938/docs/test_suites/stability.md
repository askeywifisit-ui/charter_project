# Stability Suite — Test Cases（目前平台）



---

## 來源與下載

- GitHub scripts 目錄：<https://github.com/askeywifisit-ui/charter_project/tree/main/scripts/stability>

- GitHub scripts（stability 目錄）：<https://github.com/askeywifisit-ui/charter_project/blob/main/scripts/stability>

### Export script zip（API）

> 說明：`script_id` 可能因 delete/import 變動；建議以 `suite+name` 查到 id 後再 export。

```bash
export CONTROL_PC_IP="172.14.1.140"
export CHARTER_BASE="http://${CONTROL_PC_IP}:5173"
export SUITE="<fill>"
export NAME="stability"

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
> 這頁是 **case 目錄**（列出有哪些 stability scripts），不是教學。
> - 如何跑/看結果：請看 [User Guide → Runs 操作](/user_guide/runs/)
> - 如何調整 cycles/interval（長跑前必做）：請看 [Runbook → Cycles 調整](/runbook/cycles_edit/)
> - 交付/換環境：請看 [Hand-off（交付外部單位）](/handoff/index/)

> 來源：`GET /api/scripts?suite=stability`

共 **11** 筆（按名稱排序）：

- A2435635_Continuously_executing_speedtest
- A2435637_Continuously_executing_FactoryReset
- A2435638_Cycle_power_on_off_test
- A2844344_Continuously_executing_reboot
- C15806945_WiFi_radio_enable_disable_longrun
- C24532530_UPNP_enable_disable_longrun
- C24541454_Multiple_reboot_stress
- C24541455_Multiple_speedtest
- C4123492_IPv4_Stability_Test_from_LAN_Client
- C4123494_IPv6_Stability_Test_from_LAN_Client
- C6376350_WiFi_radio_enable_disable-xtime

> 建議：交付外部單位時，除了清單外，也要說明每個 stability script 的 cycles/interval 預設值，以及是否會 reboot / power-cycle。

## 詳細說明（逐條）
- [A2435635_Continuously_executing_speedtest](stability/A2435635_Continuously_executing_speedtest/)
- [A2435637_Continuously_executing_FactoryReset](stability/A2435637_Continuously_executing_FactoryReset/)
- [A2435638_Cycle_power_on_off_test](stability/A2435638_Cycle_power_on_off_test/)
- [A2844344_Continuously_executing_reboot](stability/A2844344_Continuously_executing_reboot/)
- [C15806945_WiFi_radio_enable_disable_longrun](stability/C15806945_WiFi_radio_enable_disable_longrun/)
- [C24532530_UPNP_enable_disable_longrun](stability/C24532530_UPNP_enable_disable_longrun/)
- [C24541454_Multiple_reboot_stress](stability/C24541454_Multiple_reboot_stress/)
- [C24541455_Multiple_speedtest](stability/C24541455_Multiple_speedtest/)
- [C4123492_IPv4_Stability_Test_from_LAN_Client](stability/C4123492_IPv4_Stability_Test_from_LAN_Client/)
- [C4123494_IPv6_Stability_Test_from_LAN_Client](stability/C4123494_IPv6_Stability_Test_from_LAN_Client/)
- [C6376350_WiFi_radio_enable_disable-xtime](stability/C6376350_WiFi_radio_enable_disable-xtime/)

---

## 執行前提醒：stability cycles 設定

- stability 類腳本通常用來做「長時間/多 cycles」的穩定度與效能觀察，但平台上的 manifest 可能預設 `CYCLES=1`（方便冒煙）。
- 正式長跑前，請先用 **OpenClaw 測試助理** 進行：
  - **單次修改**（只調整某一支 script 的 `CYCLES` / `CYCLE_INTERVAL`）
  - **批次修改**（一口氣調整整個 stability suite）
- 詳細操作：請見 [Runbook → Cycles 調整（OpenClaw 測試助理）](/runbook/cycles_edit/)
- 調整完成後再 run，避免跑完才發現只跑 1 cycle。
