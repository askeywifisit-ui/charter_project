# collect_cpe_logs.py

CPE Log 收集工具。

---

## 位置

`/home/da40/charter/tools/collect_cpe_logs.py`

---

## 功能

- 收集 CPE Log
- 自動命名並存檔

---

## 常用指令

```bash
# 收集 Log
python3 /home/da40/charter/tools/collect_cpe_logs.py <RUN_ID> <REASON>
```

---

## 參數說明

| 參數 | 說明 |
|------|------|
| `RUN_ID` | 執行 ID |
| `REASON` | 收集原因（可選） |
| `--force` | 強制收集 |

---

## 使用時機

腳本執行失敗時收集 CPE Log 以供排查。
