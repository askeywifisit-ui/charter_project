# cpe_console_serial.py

Serial Console 控制工具。

---

## 位置

`/home/da40/charter/tools/cpe_console_serial.py`

---

## 功能

- Serial Console 存取
- 執行 Console 命令
- 取得 node-id

---

## 常用指令

```bash
# 執行命令
python3 /home/da40/charter/tools/cpe_console_serial.py --device /dev/ttyUSB0 --user operator shell <COMMAND>

# 取得 node-id
python3 /home/da40/charter/tools/cpe_console_serial.py --device /dev/ttyUSB0 --user operator node-id
```

---

## 參數說明

| 參數 | 說明 |
|------|------|
| `--device` | Serial 設備 |
| `--baud` | 鮎率（預設 115200） |
| `--user` | 登入帳號 |
| `--password` | 密碼 |
