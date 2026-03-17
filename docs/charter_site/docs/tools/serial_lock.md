# serial_lock.py

Serial 獨占工具，用於確保同時只有一個腳本使用 Serial。

---

## 位置

`/home/da40/charter/tools/serial_lock.py`

---

## 功能

- 取得 Serial 獨占權
- 釋放 Serial 獨占權

---

## 常用指令

```bash
# 取得獨占權
python3 /home/da40/charter/tools/serial_lock.py --acquire

# 釋放獨占權
python3 /home/da40/charter/tools/serial_lock.py --release
```

---

## 使用時機

當多個腳本可能同時訪問 Serial 時使用，確保互斥。

```python
import subprocess

# 取得權限
subprocess.run(['python3', '/home/da40/charter/tools/serial_lock.py', '--acquire'])

# ... 執行需要 Serial 的操作 ...

# 釋放權限
subprocess.run(['python3', '/home/da40/charter/tools/serial_lock.py', '--release'])
```
