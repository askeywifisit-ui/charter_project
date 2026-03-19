# OpenClaw 測試助理 Setup（交付版）

> 官方文件：https://docs.openclaw.ai

本頁目的：讓其他單位在一台乾淨的機器上，完成並驗證：
1. 安裝 OpenClaw
2. 設定 LLM（ChatGPT/OpenAI、NVIDIA Build 或 Minimax）
3. 串接 Telegram（收發訊息）
4. 用 Control UI/WebChat 驗證可用

---

## 🎯 我是誰？（快速了解）

| 問題 | 答案 |
|------|------|
| 這是什麼？ | Charter 測試平台的 AI 助理 |
| 做什麼用的？ | 自動化測試、故障排除、監控 |
| 要多少時間？ | 約 30 分鐘（不含網路問題） |

---

## 📦 我需要什麼？（前置需求）

### 硬體
- 電腦 1 台（macOS 或 Linux）
- 網路（能連 Internet）

### 軟體
- Node.js v22+
- Git

### 帳號（依需求申請）
| 服務 | 用途 | 申請方式 |
|------|------|----------|
| OpenAI API | LLM（可選） | https://platform.openai.com |
| NVIDIA Build | Kimi LLM（可選） | https://build.nvidia.com |
| Minimax API | LLM（可選） | https://platform.minimax.io |
| Telegram Bot | 訊息通知（可選） | @BotFather |

---

## ⏱️ 安裝流程時間估計

| 步驟 | 需要時間 | 備註 |
|------|----------|------|
| 1. 安裝 OpenClaw | 5 分鐘 | 網路順暢時 |
| 2. 驗證 UI | 2 分鐘 | |
| 3. 設定 LLM | 5 分鐘 | 申請 API Key 另計 |
| 4. 串接 Telegram | 5 分鐘 | 可選 |
| 5. 驗證完成 | 3 分鐘 | |
| **總計** | **約 20 分鐘** | 不含申請帳號時間 |

---

## 快速完成清單

| 步驟 | 驗證方式 |
|------|----------|
| 1. OpenClaw 安裝 | `openclaw gateway status` 顯示正常 |
| 2. Control UI 可用 | http://127.0.0.1:18789/ 能開啟 |
| 3. Chat 能回覆 | 發送「請回覆 OK」能得到回覆 |
| 4. 模型切換正常 | 切換模型後仍能正常回覆 |

---

## 安裝流程

### Step 1：安裝 OpenClaw

```bash
# 檢查版本
node -v
npm -v

# 安裝
npm i -g openclaw

# 驗證
openclaw --version
openclaw gateway status || true

# 啟動
openclaw gateway start
openclaw gateway status
```

---

## 遠程安裝指南（SSH 遠程部署）

如果你沒有直接在伺服器上操作，可以透過 SSH 遠程安裝。

### 前置準備

#### 1. 產生 SSH Key

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

#### 2. 複製 SSH 公鑰到伺服器

```bash
ssh-copy-id -i ~/.ssh/id_ed25519.pub <使用者>@<伺服器IP>
```

#### 3. 驗證 SSH 連線

```bash
ssh <使用者>@<伺服器IP> "echo 'SSH 連線成功！'"
```

---

### 安裝流程（遠程執行）

#### Step 1：安裝必要軟體

```bash
# 安裝 curl（如果沒有）
ssh <使用者>@<伺服器IP> "sudo apt-get update && sudo apt-get install -y curl"

# 安裝 Git
ssh <使用者>@<伺服器IP> "sudo apt-get install -y git"

# 安裝 Node.js 22
ssh <使用者>@<伺服器IP> "curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - && sudo apt-get install -y nodejs"

# 驗證
ssh <使用者>@<伺服器IP> "node -v && npm -v"
```

#### Step 2：安裝 OpenClaw

```bash
# 全域安裝 OpenClaw
ssh <使用者>@<伺服器IP> "sudo npm i -g openclaw"

# 驗證版本
ssh <使用者>@<伺服器IP> "openclaw --version"
```

#### Step 3：初始化與配置

```bash
# 安裝 systemd 服務
ssh <使用者>@<伺服器IP> "openclaw gateway install"

# 配置 gateway
ssh <使用者>@<伺服器IP> "openclaw config set gateway.bind lan"

# 設定 LLM API Key（以 Minimax 為例）
ssh <使用者>@<伺服器IP> "systemctl --user set-environment MINIMAX_API_KEY='你的API_KEY'"

# 設定預設模型
ssh <使用者>@<伺服器IP> "openclaw config set agents.defaults.model.primary 'minimax/MiniMax-M2.5'"
```

#### Step 4：啟動與驗證

```bash
# 啟動 Gateway
ssh <使用者>@<伺服器IP> "openclaw gateway start"

# 檢查狀態
ssh <使用者>@<伺服器IP> "openclaw gateway status"
```

---

### 訪問 Control UI

#### 方法一：SSH Tunnel（推薦）

```bash
ssh -N -L 18789:127.0.0.1:18789 <使用者>@<伺服器IP>
```

然後訪問：http://localhost:18789

#### 方法二：直接訪問

http://172.14.1.200:18789

---

### 常見問題

| 問題 | 解決方式 |
|------|----------|
| npm 安裝權限問題 | 使用 `sudo npm i -g openclaw` |
| Gateway 啟動失敗 | 執行 `openclaw doctor --fix` |
| CORS 錯誤 | 設定 `gateway.controlUi.allowedOrigins` |
| 模型無法使用 | 確認 API Key 已正確設定 |

---

### 筆記

| 項目 | 值 |
|------|-----|
| 伺服器 IP | 172.14.1.200 |
| 使用者 | da40 |
| Gateway 端口 | 18789 |
| 模型 | minimax/MiniMax-M2.5 |


> 若要開機自動啟動：用 LaunchAgent（macOS）或 systemd（Linux）。

---

### Step 2：開啟 Control UI

- **Dashboard**：http://127.0.0.1:18789/

驗證：打開 UI 後，在 Chat 發送 `請回覆 OK` → 應能得到回覆。

---

### Step 3：設定 LLM

> 原則：key 放環境變數或私密檔（權限 600），不要寫入 git。

#### OpenAI（ChatGPT）

```bash
export OPENAI_API_KEY="sk-..."
```

#### NVIDIA Build（Kimi）

```bash
export NVIDIA_API_KEY="nvapi-..."
```

設定參考：
- **Base URL**：`https://integrate.api.nvidia.com/v1`
- **Model**：`moonshotai/kimi-k2.5`

#### Minimax

```bash
export MINIMAX_API_KEY="<YOUR_KEY>"
```

設定參考：
- **Base URL**：`https://api.minimax.chat/v1`
- **Model**：`MiniMax-M2.5`

驗證：在 UI 發送 `請回覆 OK`。

---

### Step 4：串接 Telegram（可選）

#### 建立 Bot

1. 找 @BotFather
2. 送 `/newbot`
3. 取得 Bot Token（不要入 git）

#### 設定 Channel

```bash
# 驗證
openclaw channel list telegram
```

#### 驗證

從 Telegram 對 bot 發 `hi` → 應能回覆。

---

### Step 5：驗證完成

從 Control UI 或 Telegram 發送測試訊息，確認回覆正常。

---

## ❓ 遇到問題怎麼辦？

| 問題 | 處理方式 |
|------|----------|
| 安裝失敗 | 檢查 Node.js 版本（需 v22+） |
| UI 沒回覆 | 檢查 `openclaw gateway status` |
| 模型無法使用 | 確認 API Key 正確 |
| TLS 憑證錯誤 | 參考下方「TLS 處理」章節 |
| Telegram 沒訊息 | 檢查 Bot Token 與設定 |

### TLS 憑證錯誤（企業網路常見）

症狀：
- `fetch failed`
- `UNABLE_TO_GET_ISSUER_CERT_LOCALLY`

處理（macOS）：
```bash
# 匯出 System Roots
security find-certificate -a -p /System/Library/Keychains/SystemRootCertificates.keychain > ~/.openclaw/certs/system-roots.pem

# 設定環境變數
export NODE_EXTRA_CA_CERTS=~/.openclaw/certs/system-roots.pem

# 重啟
openclaw gateway restart
```

---

## 📋 交付檢查清單（交給你的人要勾）

| 項目 | 確認 |
|------|------|
| OpenClaw 版本 | <填入版本> |
| Node 版本 | <填入版本> |
| 使用模型 | <填入型號> |
| Secrets 管理 | 環境變數 / tokenFile |
| Telegram | <已設定/未設定> |

---

## 📞 聯絡資訊

- **技術窗口**：DA40 CSIT 團隊
- **文件站**：http://172.14.1.140:8000/
- **問題回報**：請附上錯誤訊息與操作步驟

---

## 相關頁面

- [Platform Links](/platform_links/)
- [Tools 工具模組](/tools/)
- [Architecture 架構](/architecture/topology/)
