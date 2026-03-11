# PDU 電源控制（MSNSwitch/UIS & DLI Web Power Switch）

本頁說明 Charter 平台目前已支援的兩種 PDU 品牌/介面，以及在平台上的設定方式。

> 風險提醒：PDU 控制屬於 **高風險操作**（會中斷 DUT 供電）。在交付/移植前必須確認 outlet mapping 正確。

---

## 1) 已支援的 PDU 品牌（目前 2 種）

| 工具 | PDU 品牌/型號線索 | 介面 | 主要 API/行為 |
|---|---|---|---|
| `pdu_outlet1.py` | `MSNSwitch/UIS` | HTTP API | `POST /api/status`、`POST /api/control` |
| `pdu_outlet2.py` | `WEBPOWERSWITCH.COM`（DLI Web Power Switch） | HTTP（DLI Web UI/控制介面） | 以 DLI 的 outlet index 控制 ON/OFF/RESET |

來源（實機程式碼註記）：
- `pdu_outlet1.py`：`PDU_BRAND = "MSNSwitch/UIS"`
- `pdu_outlet2.py`：`PDU_BRAND = "WEBPOWERSWITCH.COM"`

---

## 2) 在平台上怎麼接（你要設定哪幾個參數）

PDU 的控制點通常由 **systemd（worker）環境變數**提供：

- `PDU_SCRIPT`：要用哪支控制程式（`pdu_outlet1.py` 或 `pdu_outlet2.py`）
- `PDU_OUTLET_ID`：DUT 實際插在哪個 outlet（1-based）

> 建議：把 `PDU_SCRIPT/PDU_OUTLET_ID` 放在 `charter-worker.service` 的 Environment（或 drop-in），不要寫死在每個 script 的 manifest。

---

## 3) 常用 CLI（同事速查）

```bash
# 先確認腳本存在
ls -la /home/da40/charter/tools/pdu_outlet*.py

# 看 help（每支工具支援 on/off/reset/status）
python3 /home/da40/charter/tools/pdu_outlet1.py --help | head
python3 /home/da40/charter/tools/pdu_outlet2.py --help | head

# 最常用：看狀態
python3 /home/da40/charter/tools/pdu_outlet1.py status

# 高風險：斷電/上電/重置
python3 /home/da40/charter/tools/pdu_outlet1.py off
python3 /home/da40/charter/tools/pdu_outlet1.py on
python3 /home/da40/charter/tools/pdu_outlet1.py reset
```

---

## 4) 設定方式（Environment variables）

兩支工具都支援用環境變數覆蓋（以下為常見項）：

- `PDU_IP`
- `PDU_USER`
- `PDU_PASS`
- `PDU_OUTLET_ID`
- `PDU_TIMEOUT`
- `PDU_PROTOCOL`（`pdu_outlet1.py` 使用，預設 `http`）
- `PDU_VERIFY_SSL`（https + 自簽時才需要調整）

> 注意：`PDU_PASS` 屬敏感值，請放在 `.secrets/dut.env`，不要放在文件站。

---

## 5) 移植/交付注意事項（必讀）

1) **Outlet mapping 要先確認**
- 先在現場用 `status` 確定你控制的是正確 outlet
- 再做 `off/on/reset`

2) **外部環境沒有 PDU 的話**
- 請移除/留空 `PDU_SCRIPT/PDU_OUTLET_ID`
- 並確認依賴 power-cycle 的 stability case 要禁跑/skip/調整前置

3) **Serial 靜默（mute）行為**
- 兩支工具都有「全域 serial mute 檔」機制（避免 reboot/power-cycle 時 console 噪音干擾）
- 相關檔案：`/home/da40/charter/var/serial.mute`
