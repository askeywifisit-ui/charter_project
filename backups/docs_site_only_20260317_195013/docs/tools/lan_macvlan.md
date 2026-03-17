# lan_macvlan.py

MACVLAN 介面建立工具，用於模擬 LAN Client。

---

## 位置

`/home/da40/charter/tools/lan_macvlan.py`

---

## 功能

- 建立 MACVLAN 介面
- 在 namespace 中運作
- DHCP renew
- Ping 測試

---

## 常用指令

```bash
# 建立 MACVLAN 並 DHCP
python3 /home/da40/charter/tools/lan_macvlan.py --parent eno2 --renew

# 建立並 ping 測試
python3 /home/da40/charter/tools/lan_macvlan.py --parent eno2 --renew --ping 8.8.8.8

# 釋放並重新取得 IP
python3 /home/da40/charter/tools/lan_macvlan.py --parent eno2 --release-then-renew
```

---

## 參數說明

| 參數 | 說明 |
|------|------|
| `--parent` | 父介面（如 eno2） |
| `--ns` | namespace 名稱 |
| `--iface` | MACVLAN 介面名稱 |
| `--mac` | 指定 MAC 位址 |
| `--renew` | DHCP renew |
| `--release-then-renew` | 釋放後重新取得 |
| `--ping` | Ping 測試 |

---

## 使用時機

模擬 LAN Client 進行 DHCP/路由測試。

---

## 腳本調用範例

```python
import subprocess

result = subprocess.run([
    'python3', '/home/da40/charter/tools/lan_macvlan.py',
    '--parent', 'eno2',
    '--renew',
    '--json'
], capture_output=True, text=True)
print(result.stdout)
```
