# Environment Template（給外部單位 / 換環境必讀）

這一章的用途：當你把 Charter 平台交付給「其他單位 / 另一個 Lab / 另一套網段」時，快速列出**哪些參數需要替換**、以及建議放在哪裡（systemd / dut.env / manifest）。

> 原則：文件內看到像 **`{{CONTROL_PC_IP}}`**、**`{{WIFI_IFACE}}`** 這種 `{{...}}` 佔位符（placeholder），都代表要依你的環境實際值替換。

---

## 0) 這些參數要填到哪裡？（最重要）

先講結論：環境參數不是全部都寫在 scripts 的 manifest。

| 類型 | 建議放哪裡 | 例子 | 原因 |
|---|---|---|---|
| 平台固定（同一台 control PC 固定） | **systemd**（`/etc/systemd/system/charter-worker.service` 的 `Environment=` 或 drop-in） | `LAN_PARENT_IFACE` / `WIFI_IFACE` / `PING_IFACE` / `CPE_DEV` / `PDU_*` / `TEST_PROFILE` | 避免每個 script manifest 寫死，移植時只改一處 |
| 敏感值（不可進 repo/文件站） | **`/home/da40/charter/.secrets/dut.env`**（worker 以 `EnvironmentFile=` 讀取） | `WAREHOUSE_PASSWORD` / `SSH_PASSWORD` / 各種 token | 權限控管、交付安全 |
| NOC profiles（含 email/password） | **`/home/da40/charter/.secrets/noc_profiles.json`** | `PROFILES_FILE` 指向此檔、`NOC_PROFILE` 選 profile 名稱 | 避免在 manifest 寫死帳密 |
| scripts 的非敏感參數（case 行為） | script zip 內的 **`manifest.yaml` env**（已在文件站用 `<fill>` 去敏） | `CYCLES`/`STOP_ON_FAIL`/timeout/retry | 每個 case 不同，適合留在 manifest |

> 你如果只想快速讓平台跑起來：先把 systemd（worker）環境參數與 `.secrets/` 配好，scripts manifest 大多不用動。

---

## 0.1) 11F_140 參考值（可直接 copy／照填）

> 這段是給內部同仁最常用的「快速複製」。**不含任何密碼**。

### A) systemd（charter-worker.service）平台固定參數

把下列參數設定在 **worker 的 systemd Environment**（建議用 drop-in override，不要直接改原始 service 檔）。

11F_140 實機值：

```bash
# 11F_140 (172.14.1.140) 平台固定參數
WIFI_IFACE=wlx6cb0ce1ff230
LAN_PARENT_IFACE=eno2
PING_IFACE=eno2
CPE_DEV=/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_B0008Z1P-if00-port0
PDU_SCRIPT=/home/da40/charter/tools/pdu_outlet1.py
PDU_OUTLET_ID=1
TEST_PROFILE=lab
```

**建議寫法（對方 control PC 上直接貼）**：

```bash
sudo mkdir -p /etc/systemd/system/charter-worker.service.d
sudo tee /etc/systemd/system/charter-worker.service.d/override.conf >/dev/null <<'EOF'
[Service]
# platform-fixed params (edit for your machine)
Environment=WIFI_IFACE=wlx6cb0ce1ff230
Environment=LAN_PARENT_IFACE=eno2
Environment=PING_IFACE=eno2
Environment=CPE_DEV=/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_B0008Z1P-if00-port0
Environment=PDU_SCRIPT=/home/da40/charter/tools/pdu_outlet1.py
Environment=PDU_OUTLET_ID=1
Environment=TEST_PROFILE=lab
# optional DUT overrides
EnvironmentFile=-/home/da40/charter/.secrets/dut.env
EOF

sudo systemctl daemon-reload
sudo systemctl restart charter-worker.service
sudo systemctl status charter-worker.service --no-pager
```

### B) `.secrets/dut.env`（敏感值：只給 template）

請在對方 control PC 建立：`/home/da40/charter/.secrets/dut.env`（權限 600）。

```bash
sudo install -d -m 700 -o da40 -g da40 /home/da40/charter/.secrets
sudo -u da40 tee /home/da40/charter/.secrets/dut.env >/dev/null <<'EOF'
# Put secrets here (DO NOT commit)
# Example:
# WAREHOUSE_PASSWORD=<fill>
# SSH_PASSWORD=<fill>
EOF
chmod 600 /home/da40/charter/.secrets/dut.env
```

### C) `noc_profiles.json`（NOC email/password 放這裡，不進 manifest）

檔案位置（固定）：`/home/da40/charter/.secrets/noc_profiles.json`

```json
{
  "SPECTRUM_INT": {
    "base": "https://piranha-int.tau.dev-charter.net",
    "email": "<fill>",
    "password": "<fill>"
  }
}
```

scripts 只需要指：
- `PROFILES_FILE=/home/da40/charter/.secrets/noc_profiles.json`
- `NOC_PROFILE=SPECTRUM_INT`
- `CUSTOMER_ID=<fill>`

---

## 1) 平台（Control PC）
- Control PC（目前環境）：`{{CONTROL_PC_IP}}`（例：`172.14.1.140`）
- UI Base URL：`http://{{CONTROL_PC_IP}}:5173`
- API Base URL：`http://{{CONTROL_PC_IP}}:5173/api`

### Control PC 上的主要路徑（目前環境）
- tools：`{{TOOLS_DIR}}`（例：`/home/da40/charter/tools`）
- web：`{{WEB_DIR}}`（例：`/home/da40/charter/apps/web`）
- api（app root）：`{{API_DIR}}`（例：`/home/da40/charter/apps/api/app/`）
- data（scripts/work/venv 等）：`{{DATA_DIR}}`（例：`/home/da40/charter/data`）

---

## 2) 網路介面（有線/無線）— 必須明確註記
不同單位常見差異：Control PC 的網卡命名不同、LAN/WAN 走向不同。

> 實機對照（目前 11 LAB）：
> - 11F_140：`LAN_PARENT_IFACE=eno2`、`WIFI_IFACE=wlx6cb0ce1ff230`
> - 11F_131：`LAN_PARENT_IFACE=enx245ebe6507f7`、`WIFI_IFACE=wlan0`
> 以上僅供參考，移植時仍以 `ip link / ip route` 為準。

### 2.1 有線（LAN parent iface）
- `{{LAN_PARENT_IFACE}}`
  - 本環境例：`eno2`
  - 用途：給 `lan_macvlan.py` / LAN client 模擬用（DHCP renew/ping）

### 2.2 Wi-Fi 測試用介面
- `{{WIFI_IFACE}}`
  - 本環境例：`wlx6cb0ce1ff230`
  - 用途：iwd/nm 連線測試

### 2.3 對外 ping / route 檢查介面（可選）
- `{{PING_IFACE}}`
  - 本環境例：`eno2`
  - 用途：某些腳本會指定 ping 走哪個 iface（避免多路由時誤判）

> 建議：交付文件時，直接附上對方機器執行以下命令的輸出，避免猜測：
```bash
ip link
ip route
```

---

## 3) CPE / DUT 資訊
- CPE LAN IP：`{{CPE_HOST}}`（例：`192.168.1.1`）
- SSH user：`{{CPE_SSH_USER}}`（例：`operator`）
- SSH port：`{{CPE_SSH_PORT}}`（例：`22`）

---

## 4) PDU（電源控制，可選）

> 若你的測試流程需要「自動 reboot / power cycle / recovery」，建議配置 PDU（可由腳本或平台呼叫 API 控制插座）。
> 若未配置 PDU，部分 sanity 的前置流程可能會因 power-reset 不可用而 fail（需改成 skip/disable 該前置）。

### 4.1 PDU API 位址與白名單

- `{{PDU_IP}}`（例：`172.14.1.135`）
- PDU API endpoint（示意）：
  - `http://{{PDU_IP}}/api/status`
  - `http://{{PDU_IP}}/api/control`
- **白名單（IP Whitelist）**：
  - 至少放行 control PC：`{{CONTROL_PC_IP}}`

### 4.2 插座/Outlet 編號

- `{{PDU_OUTLET_ID}}`（例：`1`）

### 4.3 交付提醒

- 客戶環境若 PDU IP/Outlet 不同，必須替換上述欄位。
- 若客戶不提供 PDU，請在交付時明確標註：
  - 哪些 case 會依賴 PDU reset
  - 以及如何關閉/跳過 PDU 前置（避免一開始就整批 fail）

---

## 5) NOC / Cloud Profile（會因單位/環境不同而不同）

這段常見搞混點：
- `NOC_EMAIL/NOC_PASSWORD` **不要寫在 manifest**。
- 正確做法是：把 email/password 放在 `noc_profiles.json`，然後 scripts 只指定 `PROFILES_FILE + NOC_PROFILE + CUSTOMER_ID`。

你通常需要設定三個值：
- `{{NOC_PROFILE}}`（例：`SPECTRUM_INT`）→ **寫在 manifest env**（或由環境注入）
- `{{PROFILES_FILE}}`（例：`/home/da40/charter/.secrets/noc_profiles.json`）→ **指向 secrets 檔案路徑**
- `{{CUSTOMER_ID}}` → **寫在 manifest env**（或由環境注入）

> 常見失敗：`noc-context timeout`（NOC endpoint 慢/網路不通），需要調整 timeout / retry。

---

## 5) Scripts 的環境變數替換清單（交付時要列出）
以下是最常見需要替換的 env（出現在多數 sanity/stability scripts 的 manifest.yaml）：
- `TOOLS_PATH`
- `PROFILES_FILE`
- `NOC_PROFILE`
- `CUSTOMER_ID`
- `CPE_HOST`
- `LAN_PARENT_IFACE`
- `WIFI_IFACE`
- `PING_IFACE`

---

## 6) 建議交付附錄（給外部單位一次到位）
- 平台版本（web/api 版本、commit 或打包檔名）
- tools 版本（tools.tar.gz / sha256）
- scripts 匯出包（manifest.json + zip 全量）
- 一份「環境差異表」：IP/網段/網卡/SSID/權限
