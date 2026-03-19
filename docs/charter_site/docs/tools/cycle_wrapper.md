# cycle_wrapper.py

腳本入口包裝工具。

---

## 功能

- 載入 manifest.yaml 環境變數
- 支援迴圈執行
- 自動處理 JSON events

---

## 常用範例

```bash
# 在 manifest.yaml 中指定
entrypoint: cycle_wrapper.py:run

# 環境變數
CYCLES=10
CYCLE_INTERVAL=120
```

---

## 路徑

`/home/da40/charter/tools/cycle_wrapper.py`
