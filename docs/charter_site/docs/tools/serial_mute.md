# serial_mute.py

- 位置（control PC）：`/home/da40/charter/tools/serial_mute.py`

## Overview
`serial_mute.py` 是「全域 serial mute flag」工具：在 reboot/boot 期間先把 console mute 一段時間，避免：
- boot loader 被輸入干擾
- console 被其他流程搶占

它通常配合 `serial_lock.py`（互斥鎖）使用。

## 介面（節錄自 --help）
支援：`set/get/left/clear`

## 常用範例
### set 90 秒
```bash
python3 /home/da40/charter/tools/serial_mute.py set 90
# 或
python3 /home/da40/charter/tools/serial_mute.py --set 90
```

### 查剩餘秒數
```bash
python3 /home/da40/charter/tools/serial_mute.py --get
```

### clear
```bash
python3 /home/da40/charter/tools/serial_mute.py clear
```
