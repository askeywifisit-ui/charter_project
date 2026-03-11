# 平台安裝 / 移植（systemd）— 同事照做版

這頁的唯一目的：讓「第一次接手的人」照著做，就能把 Charter 平台在一台新的 control PC 上 **裝好 + 開機自動恢復（systemd 長駐）+ 跑得動腳本**。

> 安全原則：**文件站不放 NOC email/password、SSH 密碼、warehouse 密碼。**

---

## TL;DR（只想快點跑起來的人看這裡）

你要做到三件事：

1) 把 **程式**放到 `/home/da40/charter/`（web/api/tools）
2) 把 **DB（Postgres）**準備好（lab 預設 `rg/rg`）
3) 把 **systemd units**放到 `/etc/systemd/system/`，然後 `enable --now`

完成後用這三個 health check 驗證：

```bash
curl -fsSL http://127.0.0.1:8080/health
curl -fsSL http://127.0.0.1:5173/api/health
curl -fsSL http://127.0.0.1:5173/api/runs/worker/status | python3 -m json.tool
```

---

## 0) 你要先準備什麼（Checklist）

請先確認你手上有：

- **API 包**：`charter_api_<ts>.tar.gz`
- **Web 包**：`charter_web_<ts>.tar.gz`
- **Tools 包**：`charter_tools_<ts>.tar.gz`
- **Systemd units 包（11F_140 範本）**：`charter_systemd_units_11F_140_20260311_105846.tar.gz`
- OS：Ubuntu 22.04（建議）
- 帳號：`da40`（可 sudo）

> 如果是「不同單位」：另外要準備 `.secrets/`（NOC profiles / DUT env），看：
> - [Environment Template](../environment_template.md)
> - [NOC Profile / Secrets](../handoff/noc_profile_secrets.md)

---

## 1) 安裝 OS 依賴（Ubuntu 22.04）

```bash
sudo apt update
sudo apt install -y \
  python3 python3-venv python3-pip \
  postgresql postgresql-contrib \
  git unzip curl jq

sudo systemctl enable --now postgresql
```

Web 需要 Node + pnpm：

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g pnpm

node -v
pnpm -v
```

（可選）若要用 serial：
```bash
sudo usermod -aG dialout da40
# 登出再登入才生效
```

---

## 2) 解壓程式到固定路徑（/home/da40/charter）

```bash
sudo mkdir -p /home/da40/charter
sudo chown -R da40:da40 /home/da40/charter

cd /home/da40/charter

tar -xzf /path/to/charter_api_<ts>.tar.gz
tar -xzf /path/to/charter_web_<ts>.tar.gz
tar -xzf /path/to/charter_tools_<ts>.tar.gz
```

完成後你至少要看得到：
- `/home/da40/charter/apps/api/`
- `/home/da40/charter/apps/web/`
- `/home/da40/charter/tools/`

---

## 3) DB 建立（lab 預設：rg/rg）

```bash
sudo -iu postgres
psql -c "CREATE USER rg WITH PASSWORD 'rg';" || true
psql -c "CREATE DATABASE rg OWNER rg;" || true
psql -c "GRANT ALL PRIVILEGES ON DATABASE rg TO rg;" || true
exit

psql -h 127.0.0.1 -U rg -d rg -c '\\conninfo'
```

> 注意：乾淨環境通常還需要 schema（表）初始化；若你跑起來後 API/worker 報 table 不存在，請走「schema-only 匯入」或「完整 DB 還原」。

---

## 4) 安裝 systemd units（對方 control PC：照貼就能啟動）

> 情境：對方 control PC **不能**連 11F_140。
> 你只要把 units tar.gz 拿到手，照下面貼上即可。

```bash
# (A) 解壓 unit 到 /etc/systemd/system
PKG=/path/to/charter_systemd_units_11F_140_20260311_105846.tar.gz
sudo tar -xzf "$PKG" -C /etc/systemd

# (B) 重載 systemd
sudo systemctl daemon-reload

# (C) 啟用並啟動（reboot 後自動恢復）
sudo systemctl enable --now charter-api.service \
  charter-worker.service \
  cpe-metrics-agent.service \
  cpe-status-probe.timer \
  charter-web.service \
  pbr-watchdog.service

# (D) 看狀態（至少確認 api/worker/web）
sudo systemctl status charter-api.service charter-worker.service charter-web.service --no-pager
```

---

## 5) 健康檢查（必做）

```bash
# API health
curl -fsSL http://127.0.0.1:8080/health

# Web 同源 API health
curl -fsSL http://127.0.0.1:5173/api/health

# Worker
curl -fsSL http://127.0.0.1:5173/api/runs/worker/status | python3 -m json.tool
```

---

## 6) 下一步：環境配置（不同單位一定要看）

平台 service 起來後，下一步就是把「環境變動值」填齊（網卡/CPE/NOC profiles/secrets）。請依序看：

1) [Environment Template（哪些欄位要替換）](../environment_template.md)
2) [NOC profile / secrets（放哪裡、權限、template）](../handoff/noc_profile_secrets.md)
3) [交付環境表（同事照填）](../handoff/handoff_env_form.md)
4) [Network iface 指南（最常踩雷）](../handoff/network_iface_guide.md)
5) 驗證：
   - [Quick Start（10 分鐘確認平台可用）](quick_start.md)
   - [驗證步驟（快速驗證）](../handoff/handoff_validation.md)

---

## 7) 常見問題（同事最常卡）

- UI 打得開但 `/api/...` timeout：先看 `systemctl status charter-api.service`。
- run queued 卡住：先看 `systemctl status charter-worker.service` + worker status API。
- 1015/429（trycloudflare）：請改用內網 IP（`http://<control_pc_ip>:8000`）或 named tunnel 固定網址。

---

??? note "（可選）單檔下載 unit（備用）"

    - [`charter-api.service`](../assets/systemd/11F_140/etc/systemd/system/charter-api.service)
    - [`charter-worker.service`](../assets/systemd/11F_140/etc/systemd/system/charter-worker.service)
    - [`charter-web.service`](../assets/systemd/11F_140/etc/systemd/system/charter-web.service)
    - [`cpe-metrics-agent.service`](../assets/systemd/11F_140/etc/systemd/system/cpe-metrics-agent.service)
    - [`cpe-status-probe.service`](../assets/systemd/11F_140/etc/systemd/system/cpe-status-probe.service)
    - [`cpe-status-probe.timer`](../assets/systemd/11F_140/etc/systemd/system/cpe-status-probe.timer)
    - [`pbr-watchdog.service`](../assets/systemd/11F_140/etc/systemd/system/pbr-watchdog.service)
    - drop-in：[`charter-api.service.d/10-db.conf`](../assets/systemd/11F_140/etc/systemd/system/charter-api.service.d/10-db.conf)

??? note "（可選）一鍵重啟（11 LAB：restart.all.charter.sh）"

    11 LAB 現行 control PC 內有：`/home/da40/charter/restart.all.charter.sh`

    stop/start 順序摘要：
    1) stop：web → probe.timer → metrics → worker → api → watchdog
    2) daemon-reload
    3) start：api → worker → metrics → probe.timer → web → watchdog

??? note "（可選）11F_140 unit 節錄（只做對照，不給對方 copy）"

    ```bash
    sudo systemctl cat charter-worker.service
    sudo systemctl cat charter-api.service
    sudo systemctl cat charter-web.service
    sudo systemctl cat cpe-metrics-agent.service
    sudo systemctl cat cpe-status-probe.service
    sudo systemctl cat cpe-status-probe.timer
    sudo systemctl cat pbr-watchdog.service
    ```
