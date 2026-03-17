# serial_lock.py

- 位置（control PC）：`/home/da40/charter/tools/serial_lock.py`

## Overview
`serial_lock.py` 提供 serial console 操作的**互斥鎖**（file lock），避免多個腳本同時操作 serial 導致死鎖或互相干擾。

- lock 檔預設：`/home/da40/charter/var/serial.lock`（可用 `SERIAL_LOCK_PATH` 覆蓋）
- 預設不輸出 log（避免干擾 stdout 解析）；可用 `SERIAL_LOCK_LOG=1` 打開

## 使用方式（重要）
此檔案主要是提供 **Python import** 的 context manager：

```python
from serial_lock import acquire

with acquire(block=True, timeout=120):
    # do serial/console operations
    ...
```

> 它不是一個「有 --help 的 CLI 工具」（所以 `--help` 沒輸出是正常的）。

## 常見問題
- 卡住拿不到鎖：通常是前一個流程沒正常釋放或 timeout 太短
- 建議在 reboot 流程周邊使用 lock + mute
