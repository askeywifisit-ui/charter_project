# cpe_ssh.py

- 位置（control PC）：`/home/da40/charter/tools/cpe_ssh.py`

## Overview
`cpe_ssh.py` 是 Charter tools 裡的**SSH 萬用工具**，用來從 control PC（TP）連到 DUT/CPE（通常是 `192.168.1.1`）執行各種查詢/驗證，並支援 **logpull 下載**。

典型用途：
- 取得 Wi‑Fi SSID/PSK（`wifi-creds`）
- reboot（含 serial mute）
- DHCP reserved/leased table dump
- UPnP process/log 檢查
- pull-log（抓 CPE 端 tar.gz）

## CLI 介面（節錄自 --help）
### 必填參數
- `--host <ip>`

### 常用參數
- `--user <user>`（例：`operator`）
- `--password <pwd>`
- `--timeout <sec>`
- `--bind-src <ip>`：指定 control PC 的來源 IP（用來控制走哪張 NIC；同 `SSH_BIND_SRC`）
- `--cmd <subcommand>`：功能指令（下方列出常用）
- `--json`：輸出 JSON（部分 cmd 會回 `{ok, ...}`）

### 支援的 cmd（常用子集合）
- `health` / `uptime` / `ping`
- `wifi-creds`
- `reboot`
- `pull-log`
- `dhcp-reserved` / `dhcp-leased` / `dhcp`
- `wifi-radio-state` / `wifi-vif-state`
- `upnp-ps` / `upnp-proc` / `upnp-log`

> 完整列表請執行：`python3 /home/da40/charter/tools/cpe_ssh.py --help`

## 常用範例（建議照抄）
### 1) 最小連線測試
```bash
python3 /home/da40/charter/tools/cpe_ssh.py \
  --host 192.168.1.1 --user operator --password '<fill>' \
  --cmd uptime --json
```

### 2) 取得 Wi‑Fi creds（SSID/PSK）
```bash
python3 /home/da40/charter/tools/cpe_ssh.py \
  --host 192.168.1.1 --user operator --password '<fill>' \
  --cmd wifi-creds --which both --json
```

### 3) 抓 DHCP reserved / leased
```bash
python3 /home/da40/charter/tools/cpe_ssh.py --host 192.168.1.1 --user operator --password '<fill>' --cmd dhcp-reserved --json
python3 /home/da40/charter/tools/cpe_ssh.py --host 192.168.1.1 --user operator --password '<fill>' --cmd dhcp-leased   --json
```

### 4) pull-log（下載 CPE logpull 壓縮檔）
```bash
python3 /home/da40/charter/tools/cpe_ssh.py \
  --host 192.168.1.1 --user operator --password '<fill>' \
  --cmd pull-log \
  --latest-from-dir /tmp/logpull --pattern '*.tar.gz' \
  --dest /tmp/cpe_log \
  --pre-logpull --logpull-timeout 120 \
  --rename-with-node-id
```

## 輸出（概念）
- 多數腳本只看：`ok`、`rc`、以及必要欄位（ssid/psk、reserved list、etc.）
- `--debug` 可附加 raw output（排障用）

## 常見問題 / 排除
- **SSH 還沒 ready / port 22 未開**：需要先 NOC ssh-enable，且 boot 後 port 22 可能延遲；建議 retry。
- **多網卡**：用 `--bind-src` 強制走 DUT LAN 那張 NIC（避免走錯路由）。
- **安全**：不要把 `--password` 直接貼到群組截圖；建議用環境變數/secret file。
