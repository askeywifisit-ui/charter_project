# pdu_outlet1.py / pdu_outlet2.py

PDU 電源控制工具。

---

## 位置

- MSNSwitch: `/home/da40/charter/tools/pdu_outlet1.py`
- DLI: `/home/da40/charter/tools/pdu_outlet2.py`

---

## 功能

- 控制 PDU 插座開關
- 電源重置
- 查詢狀態

---

## 常用指令

```bash
# 開啟插座
python3 /home/da40/charter/tools/pdu_outlet1.py on --outlet 1

# 關閉插座
python3 /home/da40/charter/tools/pdu_outlet1.py off --outlet 1

# 電源重置（關→開）
python3 /home/da40/charter/tools/pdu_outlet1.py reset --outlet 1

# 查詢狀態
python3 /home/da40/charter/tools/pdu_outlet1.py status --outlet 1
```

---

## 參數說明

| 參數 | 說明 |
|------|------|
| `on` | 開啟插座 |
| `off` | 關閉插座 |
| `reset` | 電源重置 |
| `status` | 查詢狀態 |
| `--outlet` | 插座編號 |

---

## 使用時機

- CPE 無法遠端重啟時
- 需要徹底斷電重開

---

## 腳本調用範例

```python
import subprocess

# 重置 CPE 電源
subprocess.run([
    'python3', '/home/da40/charter/tools/pdu_outlet1.py', 'reset', '--outlet', '1'
])
```
