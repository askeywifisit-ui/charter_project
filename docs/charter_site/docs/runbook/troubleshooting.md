# 故障排除（交接手冊）

> 本頁面旨在幫助 **新接手 Charter 平台** 的維運者快速上手，包含：
> - 系統基本認知
> - 優先排查方向
> - 常見問題快速解法
> - 需要escalate 時的資訊

---

## 🎯 第一步：快速健康檢查

剛接手系統時，先確認以下項目：

```bash
# 1. Charter 文件站運作中？
curl -s http://127.0.0.1:8000 | head -5

# 2. Gateway 正常運作？
openclaw gateway status

# 3. Worker 有多少？
curl -s http://127.0.0.1:8000/api/runs/worker/status | jq

# 4. Control PC 能連外網？
curl -s --connect-timeout 5 https://api.telegram.org
```

**如果全部 OK**，但用戶仍回報問題 → 往下看具體徵兆

---

## 🧩 系統基本認知

| 元件 | 用途 | 常見位置 |
|------|------|----------|
| Charter 文件站 (mkdocs) | 網頁 UI、呈現測試報告 | `http://172.14.1.140:8000` |
| Worker | 實際執行測試腳本 | Control PC |
| OpenClaw Gateway | 訊息轉發、對話控制 | `127.0.0.1:18789` |
| NOC | CPE 設備控制 API | 取決於部署環境 |

**通訊鏈路**：
```
Telegram/Line/Signal → OpenClaw Gateway → Charter API → Worker → CPE 設備
```

---

## 1) Run 一直 queued，UI 開著但卡住

**這是最常見的回報問題**。作為維運者，請按以下順序排查：

### Step 1：確認 Worker 狀態
```bash
curl http://127.0.0.1:8000/api/runs/worker/status
```

| 回應 | 意義 |
|------|------|
| `{"total": 2, "idle": 2}` | 有 worker 在閒置，問題在 queue |
| `{"total": 2, "idle": 0}` | Worker 都在忙，需要等或砍掉卡住的 task |

### Step 2：如果 Worker 全忙
```bash
# 查看正在運行的 task
curl http://127.0.0.1:8000/api/runs | jq '.[] | select(.status=="running")'
```

### Step 3：緊急處置
- SSH 進 Control PC
- 找到卡住的 worker process，kill 後重啟
- 或重啟 Charter 服務：`sudo systemctl restart charter`

### 交接備註
> **歷史經驗**：90% 的 queued 問題是因為 worker 卡住而非 queue 本身。優先檢查 worker 狀態。

---

## 2) 脚本报错：noc-context timeout

**常見錯誤**：
```
HTTPSConnectionPool(...): Read timed out (read timeout=20)
```

### 快速判斷
| 問題 | 徵兆 | 解法 |
|------|------|------|
| 網路不通 | ping / curl 都失敗 | 檢查 Control PC 網路閘道 |
| NOC 忙碌 | 偶發 timeout | 脚本加 retry（這是常態）|
| DNS 問題 | 所有 external call 都 timeout | 檢查 `/etc/resolv.conf` |

### Debug 指令
```bash
# 從 Control PC 測試 NOC 連線
curl -v --connect-timeout 10 https://<noc-endpoint>

# 檢查 DNS
nslookup <noc-endpoint>

# 檢查網路閘道
netstat -rn | grep default
```

### 交接備註
> **重要**：Control PC 通常放在實驗室，網路環境可能與辦公區不同。如果你在辦公區debug 不到問題，請直接 SSH 到 Control PC 上測試。

---

## 3) API set 成功但 CPE 端表未同步

**這不是 bug，是設計如此。**

### 為什麼會這樣？
CPE 設備（光世代 modem 等）收到 API 指令後，內部需要 **幾秒到幾十秒** 才會反應在管理 table 上。

### 正確處理方式
```python
# 錯誤示範（立即斷言）
api.set_wan(...)
assert get_wan_status() == "connected"  # 會 fail

# 正確做法
api.set_wan(...)
time.sleep(10)  # 等待 CPE 同步
for i in range(10):
    status = get_wan_status()
    if status == "connected":
        break
    time.sleep(2)
```

### 交接備註
> 如果用戶回報「API 成功但沒通」，先問：等多久？如果 <30 秒，請他再等一下。

---

## 4) Wi‑Fi / 網路介面問題

### 常見場景
腳本需要指定「從哪張網卡走」，但不同機器的介面名稱不同：

| 環境 | 常見介面名稱 |
|------|-------------|
| Linux 桌機 | `eno2`, `eth0` |
| macOS | `en0`, `en1` |
| IoT 設備 | `wlan0`, `ra0` |

### 排查步驟

**Step 1：確認本機介面**
```bash
# Linux
ip a

# macOS
ifconfig
```

**Step 2：確認 IPv6 zone id**
如果腳本用 IPv6 link-local URL：
- 正確：`http://fe80::1%25eno2`
- 錯誤：`http://fe80::1`（會連不上）

**Step 3：集中管理環境變數**
不要寫死在腳本 zip 裡，用以下方式管理：
- `.secrets/dut.env`
- systemd service 環境變數
- 或在 CI/CD pipeline 注入

---

## 5) OpenClaw / Gateway 連線問題

### 常見徵兆

| 錯誤訊息 | 原因 | 解法 |
|----------|------|------|
| `requires device identity` | HTTP + 非 localhost 被瀏覽器擋 | 用 SSH tunnel 或 HTTPS |
| `/chat` 打不開 | Gateway 沒啟動 | `openclaw gateway start` |
| Token 錯誤 | auth 設定不正確 | 檢查 `~/.openclaw/gateway.token` |

### 快速解法：SSH Tunnel

如果你在遠端需要 access：

```bash
# 將 Charter 機器的 gateway 映射到本機
ssh -L 18789:127.0.0.1:18789 csit@172.14.1.140

# 然後訪問
http://127.0.0.1:18789/chat
```

### 交接備註
> **最常用**：SSH tunnel 是最快解。不要浪費時間在設定 HTTPS，特別是臨時需要 debug 時。

---

## 6) 用戶說「不能用」但你看起來正常

這是最難 debug 的情況。按以下順序確認：

### Step 1：請用戶截圖
- 螢幕畫面
- 網址列
- 瀏覽器開發者工具（F12）Console 頁籤

### Step 2：請用戶做一個簡單動作
例如：
```bash
# 請用戶在 Telegram 打下 /status
# 觀察回覆內容
```

### Step 3：檢查對話紀錄
```bash
# 查看最近的對話
ls -la ~/.openclaw/logs/ | tail -10
```

---

## 📋 交接檢查清單

新手上路，請確認以下項目都已設定：

- [ ] 取得 Control PC SSH 權限
- [ ] 加入 Charter 文件站管理（Telegram/Line/Signal 機器人）
- [ ] 了解 NOC endpoint 在哪（問上一手或 PM）
- [ ] 知道誰負責 CPE 設備（硬體問題需要聯繫他們）
- [ ] 取得 OpenClaw Gateway token（通常在 `~/.openclaw/openclaw.json`）

---

## 🆘 需要 Escalate 時

如果以下情況，請準備向下一層級回報：

| 情況 | 回報給 | 資訊準備 |
|------|--------|----------|
| 文件站挂了 | 上一手維運 | `curl` 結果、錯誤訊息 |
| Worker 全掛 | 上一手 / PM | `systemctl status charter` 輸出 |
| NOC 全面連不上 | PM / NOC 負責人 | 測試截圖、Control PC IP |
| 硬體問題（CPE 設備不動）|  field team | 設備序號、錯誤截圖 |

---

## 📞 常用快速指令

```bash
# 確認 Charter 文件站
curl -s http://127.0.0.1:8000 | grep -i "charter"

# 確認 Worker
curl -s http://127.0.0.1:8000/api/runs/worker/status

# 確認 Gateway
openclaw gateway status

# 確認網路（從 Control PC）
curl -v --connect-timeout 5 https://api.telegram.org

# 查看今天日誌
tail -f /var/log/charter/today.log
```
