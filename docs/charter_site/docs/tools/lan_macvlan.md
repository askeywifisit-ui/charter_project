# lan_macvlan.py

- 位置（control PC）：`/home/da40/charter/tools/lan_macvlan.py`

## Overview
`lan_macvlan.py` 在 control PC 的**有線網卡**上建立 macvlan（通常搭配 netns），用來模擬一個或多個 LAN client：
- DHCP renew / rebind
- ping 驗證
- 用 JSON 回報結果給 scripts 做 assert

## 介面（節錄自 --help）
常用參數：
- `--parent <iface>`：要掛在哪張實體有線卡（例：`eno2`）
- `--iface auto`：自動取唯一的 macvlan 介面名
- `--mac 02:..`：指定固定 MAC（做 DHCP reservation 測試時很重要）
- `--renew` / `--release-then-renew`
- `--ping <host>`
- `--json`

## 常用範例
### 1) DHCP renew
```bash
python3 /home/da40/charter/tools/lan_macvlan.py \
  --parent "{{LAN_PARENT_IFACE}}" --iface auto \
  --mac '02:11:22:33:44:55' \
  --renew --json
```

### 2) renew + ping
```bash
python3 /home/da40/charter/tools/lan_macvlan.py \
  --parent "{{LAN_PARENT_IFACE}}" --iface auto \
  --mac '02:11:22:33:44:55' \
  --renew --json \
  --ping 'google.com'
```

## 常見問題 / 排除
- `LAN_PARENT_IFACE` 選錯會拿不到 DHCP：請依 Hand-off → 網卡判定指南確認
- 多路由：必要時搭配 `PING_IFACE` 或 policy routing
