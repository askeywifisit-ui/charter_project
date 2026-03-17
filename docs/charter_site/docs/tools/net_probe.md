# net_probe.py

網路探測工具，支援 ping / curl / DNS 測試，可綁定來源 IP 或介面。

---

## 功能

- **ping**：指定來源 IP 或介面
- **curl**：HTTP 請求，可綁定來源
- **DNS 查詢**：使用 dig，自動處理 systemd-resolved 問題

---

## 常用指令

```bash
# Ping 測試
python3 /home/da40/charter/tools/net_probe.py ping -h 192.168.1.1

# DNS 查詢
python3 /home/da40/charter/tools/net_probe.py dns -d google.com

# HTTP 請求
python3 /home/da40/charter/tools/net_probe.py curl http://example.com
```

---

## 路徑

`/home/da40/charter/tools/net_probe.py`
