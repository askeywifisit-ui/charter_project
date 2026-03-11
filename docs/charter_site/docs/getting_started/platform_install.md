# 平台安裝 / 移植（systemd）— 內部同事版（專業說明 + 可直接照做）

這頁的目的：讓第一次接手的人，理解「為什麼要這樣做」並且照著做就能在新的 control PC 上把 Charter 平台 **裝好、長駐、可跑腳本**。

> 安全原則：文件站不放 NOC email/password、SSH 密碼、warehouse 密碼。敏感值一律走 `.secrets/`。

---

## 成功標準（你做到這 3 件事就算平台 OK）

1) **API OK**
```bash
curl -fsSL http://127.0.0.1:8080/health
```

2) **Web 同源 API OK**（UI 會用這個路徑呼叫 API）
```bash
curl -fsSL http://127.0.0.1:5173/api/health
```

3) **Worker OK**（否則 scripts 會 queued 卡住）
```bash
curl -fsSL http://127.0.0.1:5173/api/runs/worker/status | python3 -m json.tool
```

---

## 平台架構（你在啟動什麼？）

| 元件 | systemd unit | 你需要它做什麼 |
|---|---|---|
| API | `charter-api.service` | 提供 `/api/...`（健康檢查、scripts/runs API） |
| Worker | `charter-worker.service` | 解壓 scripts zip、建立 venv、執行腳本、產出 log/archive |
| Web | `charter-web.service` | UI（並同源 proxy 到 `/api/...`） |
| Metrics（必需） | `cpe-metrics-agent.service` | 定期採集 CPE 指標送到 API（Dashboard/健康資訊依賴） |
| Probe（必需） | `cpe-status-probe.timer` | 定期探測 CPE 狀態寫 DB（平台狀態/排查依賴） |
| Watchdog（必需） | `pbr-watchdog.service` | PBR/route 守護，避免測試路由飄（確保測試流量走對） |

> 我們目前的標準平台交付/操作流程：上述 6 個 unit 都視為「必需」並預設 `enable --now`。

---

## 你要先拿到什麼（交付物 / Checklist）

先講白話：你只要拿到「4 個檔案」，其他都是照步驟解壓/啟動。

你需要這 4 個交付檔：

- API：`charter_api_<ts>.tar.gz`
- Web：`charter_web_<ts>.tar.gz`
- Tools：`charter_tools_<ts>.tar.gz`
- Systemd units（11F_140 範本）：`charter_systemd_units_11F_140_20260311_105846.tar.gz`

> 下載入口（同事最常用）：[交付下載（downloads）](../handoff/downloads.md)

### 這 4 個檔案從哪裡拿？

- 請參考：[交付下載（downloads）](../handoff/downloads.md)
  -（同事提示）打開 downloads 頁後，直接下載：scripts / web / api / tools / systemd units（皆在同一頁）

> 不同單位/不同環境一定還需要準備 `.secrets/`（NOC profiles / DUT env），否則腳本會在 NOC/SSH/warehouse 相關步驟失敗：
> - [Environment Template](../environment_template.md)
> - [NOC Profile / Secrets](../handoff/noc_profile_secrets.md)

---

## 1) OS 依賴（Ubuntu 22.04）

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

（可選）serial 權限：
```bash
sudo usermod -aG dialout da40
# 登出再登入才生效
```

---

## 2) 程式放置（固定路徑：/home/da40/charter）

> 這段同事最常要「直接複製貼上」：下面提供一個完整 block。
> 你只要把 3 個檔案路徑填好（API/Web/Tools 的 tar.gz），貼上執行即可。

```bash
# 0) 先填交付檔案路徑（依你實際放哪裡調整）
API_PKG=/path/to/charter_api_<ts>.tar.gz
WEB_PKG=/path/to/charter_web_<ts>.tar.gz
TOOLS_PKG=/path/to/charter_tools_<ts>.tar.gz

# 1) 建目錄 + 權限
sudo mkdir -p /home/da40/charter
sudo chown -R da40:da40 /home/da40/charter
cd /home/da40/charter

# 2) 解壓
sudo -u da40 tar -xzf "$API_PKG"
sudo -u da40 tar -xzf "$WEB_PKG"
sudo -u da40 tar -xzf "$TOOLS_PKG"

# 3) 驗收（缺一個都會起不來）
ls -la /home/da40/charter/apps/api/ /home/da40/charter/apps/web/ /home/da40/charter/tools/
```

為什麼要固定路徑：systemd unit 會用 `WorkingDirectory/ExecStart` 指到這些目錄，所以路徑對齊是第一優先。

---

## 3) DB（為什麼要建？）

平台用 Postgres 存 scripts/runs/worker 狀態等資料。

Lab 預設沿用 11F_140：`rg/rg`（內部環境 OK）。

```bash
sudo -iu postgres
psql -c "CREATE USER rg WITH PASSWORD 'rg';" || true
psql -c "CREATE DATABASE rg OWNER rg;" || true
psql -c "GRANT ALL PRIVILEGES ON DATABASE rg TO rg;" || true
exit

psql -h 127.0.0.1 -U rg -d rg -c '\\conninfo'
```

> 若你看到錯誤像「table does not exist」：代表 DB schema 沒初始化。
> 解法：做 schema-only 匯入或完整 DB 還原（見交付流程）。

---

## 4) systemd 長駐（對方 control PC：一段 copy/paste）

> 情境：對方 control PC **不能**連 11F_140。
> 作法：拿到 units tar.gz 後，解壓到 `/etc/systemd/system`，再 `enable --now`。

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

# (D) 立即驗收（至少確認 api/worker/web）
sudo systemctl status charter-api.service charter-worker.service charter-web.service --no-pager
```

為什麼要 `enable`：因為只 `start` 的話，reboot 後不會自動起來。

---

## 5) 驗收（必做，避免「看起來有 UI 但其實 worker 壞了」）

```bash
curl -fsSL http://127.0.0.1:8080/health
curl -fsSL http://127.0.0.1:5173/api/health
curl -fsSL http://127.0.0.1:5173/api/runs/worker/status | python3 -m json.tool
```

---

## 6) 下一步：環境配置（不同單位一定要看）

平台 service 起來後，下一步就是把「環境變動值」填齊（網卡/CPE/NOC profiles/secrets）。

1) [Environment Template（哪些欄位要替換）](../environment_template.md)
2) [NOC profile / secrets（放哪裡、權限、template）](../handoff/noc_profile_secrets.md)
3) [交付環境表（同事照填）](../handoff/handoff_env_form.md)
4) [Network iface 指南（最常踩雷）](../handoff/network_iface_guide.md)
5) 驗證：
   - [Quick Start（10 分鐘確認平台可用）](quick_start.md)
   - [驗證步驟（快速驗證）](../handoff/handoff_validation.md)

---

## 7) Troubleshooting（同事最常卡的 5 個點）

- UI 有，但 `/api/...` timeout：`systemctl status charter-api.service` + `journalctl -u charter-api.service -n 200 --no-pager`
- run queued 卡住：`systemctl status charter-worker.service` + worker status API
- Web 起不來：`systemctl status charter-web.service`（常見是 node/pnpm 沒裝或 run_web.sh 權限）
- DB 連不上：確認 `DATABASE_URL/PSQL_URL`（unit drop-in）與 Postgres running
- PBR/路由飄：先暫停 watchdog 釐清（或依環境調整 IF/SRC/GW/SUB）

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

??? note "（可選）11F_140 unit 節錄（只做對照）"

    ```bash
    sudo systemctl cat charter-worker.service
    sudo systemctl cat charter-api.service
    sudo systemctl cat charter-web.service
    sudo systemctl cat cpe-metrics-agent.service
    sudo systemctl cat cpe-status-probe.service
    sudo systemctl cat cpe-status-probe.timer
    sudo systemctl cat pbr-watchdog.service
    ```
