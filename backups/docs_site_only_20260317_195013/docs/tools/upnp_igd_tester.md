# upnp_igd_tester.py

UPnP IGD 測試工具。

---

## 位置

`/home/da40/charter/tools/upnp_igd_tester.py`

---

## 功能

- SSDP M-SEARCH 掃描
- 抓取 IGD 描述
- 測試 UPnP Port Mapping

---

## 常用指令

```bash
# 測試 UPnP
python3 /home/da40/charter/tools/upnp_igd_tester.py --iface eno2
```

---

## 功能說明

1. 從指定介面取得 IPv4
2. SSDP 掃描找出 IGD
3. 抓取 rootDesc.xml
4. 測試 Port Mapping：
   - GetExternalIPAddress
   - AddPortMapping
   - GetSpecificPortMappingEntry
   - DeletePortMapping
