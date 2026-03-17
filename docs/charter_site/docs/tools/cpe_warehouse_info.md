# cpe_warehouse_info.py

CPE Warehouse 資訊查詢工具。

---

## 位置

`/home/da40/charter/tools/cpe_warehouse_info.py`

---

## 功能

- 從 CPE 的 warehouse.cgi 取得資訊
- 查詢 Warehouse 資料表

---

## 常用指令

```bash
# 查詢 CPE Warehouse 資訊
python3 /home/da40/charter/tools/cpe_warehouse_info.py

# 輸出 JSON
python3 /home/da40/charter/tools/cpe_warehouse_info.py --json

# 指定欄位
python3 /home/da40/charter/tools/cpe_warehouse_info.py -f <FIELD_NAME>
```

---

## 參數說明

| 參數 | 說明 |
|------|------|
| `--user` | 帳號 |
| `--password` | 密碼 |
| `--json` | JSON 輸出 |
| `-f` | 指定欄位 |
