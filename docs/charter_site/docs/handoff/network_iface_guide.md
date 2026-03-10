# 網卡判定與替換指南（LAN/Wi‑Fi/Ping iface）

交付外部單位時，最容易出問題的是：control PC 網卡名稱不同、預設路由不同，導致腳本連不到 CPE 或 ping 走錯路。

本頁提供「怎麼找出正確的 iface」與「manifest/env 要替換哪些欄位」。

---

## 本環境參考值（11 LAB）

> 這裡列的是「我們實機上目前的設定」，方便你對照。移植到新機器仍要依本頁步驟重新判定。

| 站台 | LAN_PARENT_IFACE | WIFI_IFACE | PING_IFACE | CPE LAN |
|---|---|---|---|---|
| 11F_140（172.14.1.140） | `eno2` | `wlx6cb0ce1ff230` | `eno2` | `192.168.1.1` |
| 11F_131（172.14.1.131） | `enx245ebe6507f7` | `wlan0` | `enx245ebe6507f7` | `192.168.1.1` |

> 交付外部單位時：網卡名稱幾乎一定不同，請依本頁步驟重新判定。

## 1) 需要替換的常見欄位
- `LAN_PARENT_IFACE`：給 `lan_macvlan.py` 模擬 LAN client 用
- `WIFI_IFACE`：給 `wifi_iwd.py` / `wifi_nm.py` Wi‑Fi 連線用
- `PING_IFACE`：可選，用於指定 ping 走哪張卡（多路由時避免誤判）

---

## 2) 如何找 `LAN_PARENT_IFACE`
### (A) 列出網卡
```bash
ip link
```

### (B) 看預設路由走哪張卡
```bash
ip route | head -n 20
```

通常你會看到類似：
- `default via <gateway> dev eno2 ...`

此時 `dev eno2` 就很可能是 `LAN_PARENT_IFACE`（依你們拓撲：LAN client 模擬要掛在哪個實體介面）。

### (C) 驗證（用 lan_macvlan renew）
```bash
PARENT_IFACE='{{LAN_PARENT_IFACE}}'
MAC='02:11:22:33:44:55'
python3 /home/da40/charter/tools/lan_macvlan.py --parent "$PARENT_IFACE" --iface auto --mac "$MAC" --renew --json
```
若成功拿到 `dhcp.ipv4`，表示 iface 判定大致正確。

---

## 3) 如何找 `WIFI_IFACE`
### (A) 看無線裝置
```bash
# 若系統有 iw
iw dev

# 或用 NetworkManager
nmcli dev status
```

你會看到類似：
- `wlx6cb0ce1ff230`（USB Wi‑Fi dongle 常見）

把那個介面名填到 `WIFI_IFACE`。

### (B) 驗證（用 wifi_iwd ensure）
```bash
WIFI_IFACE='{{WIFI_IFACE}}'
WIFI_SSID='{{SSID}}'
export WIFI_PSK='{{PSK}}'
python3 /home/da40/charter/tools/wifi_iwd.py --json ensure --iface "$WIFI_IFACE" --ssid "$WIFI_SSID" --password-env WIFI_PSK --timeout 45
```

---

## 4) 何時需要 `PING_IFACE`
當 control PC 有多張網卡/多條 default route 時，ping 可能走錯出口。

### 判斷方式
```bash
ip route
```
若有多條 default、或 policy routing，建議在 scripts manifest 設 `PING_IFACE`。

---

## 5) 交付外部單位建議附錄
請對方提供以下命令輸出，便於快速定位：
```bash
ip link
ip route
nmcli dev status
```
