# cycle_wrapper.py

腳本入口包裝工具，用於載入 `manifest.yaml` 環境變數。

---

## 功能

- 載入腳本目錄下的 `manifest.yaml` 環境變數
- 支援多種 entrypoint 格式（`module:func` 或 `file.py:func`）
- 自動處理 JSON events 輸出
- 若缺少 PyYAML，會提示並 exit

---

## 使用方式

腳本 ZIP 的 `manifest.yaml` 中指定 entrypoint：

```yaml
entrypoint: cycle_wrapper.py:run
```

---

## 路徑

`/home/da40/charter/tools/cycle_wrapper.py`
