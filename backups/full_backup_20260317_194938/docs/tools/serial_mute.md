# serial_mute.py

Serial 靜音工具，用於避免 boot 過程的 Serial 輸出干擾腳本執行。

---

## 位置

`/home/da40/charter/tools/serial_mute.py`

---

## 功能

- 設定靜音時長（秒）
- 查詢剩餘靜音時間
- 清除靜音

---

## 常用指令

```bash
# 設定靜音 120 秒
python3 /home/da40/charter/tools/serial_mute.py --set 120

# 查詢剩餘時間
python3 /home/da40/charter/tools/serial_mute.py --get

# 清除靜音
python3 /home/da40/charter/tools/serial_mute.py --clear
```

---

## 使用時機

在 CPE reboot 前執行，避免 Serial 输出干扰后续测试。

```bash
# Reboot 前靜音
python3 /home/da40/charter/tools/serial_mute.py --set 120
python3 /home/da40/charter/tools/cpe_ssh.py --host 192.168.1.1 --cmd reboot
```

---

## 腳本調用範例

```python
import subprocess

# 靜音 120 秒
subprocess.run(['python3', '/home/da40/charter/tools/serial_mute.py', '--set', '120'])
```
