# pdu_outlet1.py / pdu_outlet2.py

- 位置（control PC）：
  - `/home/da40/charter/tools/pdu_outlet1.py`
  - `/home/da40/charter/tools/pdu_outlet2.py`

## Overview
這兩支工具用來控制 PDU outlet 做 power control（on/off/reset/status），常被 stability power-cycle 類腳本呼叫。

## CLI
（工具自帶 usage）
```bash
python3 /home/da40/charter/tools/pdu_outlet1.py --help
python3 /home/da40/charter/tools/pdu_outlet2.py --help
```

常用：
```bash
python3 /home/da40/charter/tools/pdu_outlet1.py status
python3 /home/da40/charter/tools/pdu_outlet1.py off
python3 /home/da40/charter/tools/pdu_outlet1.py on
python3 /home/da40/charter/tools/pdu_outlet1.py reset
```

## 風險提醒（交付必讀）
- power-cycle 屬 **高風險**（會中斷 DUT 供電）
- 交付外部單位必須確認 outlet mapping 正確
- 若外部環境沒有 PDU：power-cycle 類 stability case 必須禁跑或改實作
