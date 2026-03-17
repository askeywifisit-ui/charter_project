# OpenClaw 測試助理 Setup（交付版）

本頁目的：讓其他單位在一台乾淨的機器上，完成並驗證：
1) 安裝 OpenClaw
2) 設定 LLM（ChatGPT/OpenAI 或 Kimi via NVIDIA Build）
3) 串接 Telegram（收發訊息）
4) 用 Control UI/WebChat 驗證可用

> 原則：**不要把 API key / token 直接寫進文件 repo**。

---

## 快速完成清單（Quick Checklist）
完成以下 4 件事，就算 setup 成功：
1) `openclaw gateway status` 顯示 gateway 正常
2) Control UI（`http://127.0.0.1:18789/`）Chat 能回覆
3) Telegram bot 能回覆（DM）
4) 換成指定模型（OpenAI 或 NVIDIA Build）仍能回覆

---

## 0) 前置需求（Prerequisites）

- OS：macOS / Linux（擇一）
- Node.js：建議 v22+（本環境為 Node 22.x）
- 對外連線（至少要能通其中一個 LLM provider）：
  - OpenAI（如使用 ChatGPT/OpenAI）
  - NVIDIA Build（Kimi）
- Telegram Bot API（若要用 Telegram）
- DNS / TLS 正常
  - 若公司環境做 HTTPS inspection，可能遇到 TLS 憑證問題（可參考本頁「Troubleshooting → TLS/CA」）

建議先做基本連通測試：
```bash
curl -sS -I https://api.openai.com | head
curl -sS -I https://integrate.api.nvidia.com | head
```

---

## 1) 安裝 OpenClaw（npm global）

> 安裝方式（與 DA40 一致）：npm 全域安裝。

```bash
node -v
npm -v

npm i -g openclaw

openclaw --version
openclaw gateway status || true
```

啟動 gateway：
```bash
openclaw gateway start
openclaw gateway status
```

> 若你要「開機自動啟動」，請改用 LaunchAgent/systemd（視 OS 而定）。

---

## 2) 開啟 Control UI / WebChat

- 預設（local loopback）：
  - Dashboard: http://127.0.0.1:18789/

驗證：
- 打開 UI 後，在 Chat 分頁發送：`請回覆 OK` → 應能得到回覆（後續會切換模型驗證）。

---

## 3) LLM 設定

> 建議做法：把 key 放在「環境變數」或「私密檔（權限 600）」；不要寫入 git。

### 3.1 ChatGPT / OpenAI（可選）
- Key：`OPENAI_API_KEY`

驗證：
- 在 Control UI 送出一則訊息 → 有正常回覆即可。

### 3.2 Kimi（NVIDIA Build / OpenAI-compatible）

Kimi key 取得：
- https://build.nvidia.com/settings/api-keys

本環境使用的 NVIDIA Build 參數（範例）：
- Base URL：`https://integrate.api.nvidia.com/v1`
- Model id：`moonshotai/kimi-k2.5`
- OpenClaw model key：`nvidia/moonshotai/kimi-k2.5`

建議 key 命名：
- `NVIDIA_API_KEY="<YOUR_KEY>"`

> 交付建議：不要沿用 `OPENAI_API_KEY` 來裝 NVIDIA key，避免跟真正 OpenAI key 混淆。

驗證：
1) 在 Control UI 選用（或設定預設）模型：`nvidia/moonshotai/kimi-k2.5`
2) 發送：`請回覆 OK`
3) 預期：回覆 OK（或合理文字）

---

## 4) Telegram 串接（收發訊息）

### 4.1 建立 Telegram Bot

1) 在 Telegram 找 @BotFather
2) `/newbot`
3) 取得 **Bot Token**（不要入 repo）

### 4.2 OpenClaw 設定 Telegram channel（概念）

- 建議用 tokenFile/secret file（不要把 token 寫死在 openclaw.json 進 git）
- 建議限制：
  - DM policy：pairing
  - Group policy：allowlist

### 4.3 驗證

1) 從 Telegram 對 bot 發「hi」
2) 期待：bot 會回覆（表示 channel → gateway → LLM 完整鏈路 OK）
3) Control UI 的 Sessions/Chat 也應可看到對應 session

若你們採 pairing 流程（建議）：
```bash
openclaw pairing list telegram
openclaw pairing approve telegram <CODE>
```

---

## 5) 助理頭像（WebChat/Control UI）

正規做法（避免走 `/assets/...`）：

1) 把 icon 放到 OpenClaw workspace：

```bash
cd ~/.openclaw/workspace
mkdir -p avatars
# 放入 avatars/lina_512.png （建議 512x512）
```

2) 編輯 `~/.openclaw/workspace/IDENTITY.md`：

```text
Avatar: avatars/lina_512.png
```

3) 重啟 gateway：

```bash
openclaw gateway restart
```

若 UI 還是舊頭像：
- Hard Reload（Ctrl+Shift+R / ⌘+Shift+R）
- 或改檔名破快取（例如 `lina_512_v2.png`）再重啟。

---

## 6) 最小故障排除（Troubleshooting）

### 6.1 UI 沒回覆 / 一直顯示 …
- 先看：
  - `openclaw gateway status`
- 再看：TLS/CA 是否錯誤（見 6.4）

### 6.2 Telegram 沒訊息
- Bot token 是否正確
- allowlist / pairing 是否擋到
- gateway 是否啟動 telegram plugin/channel

### 6.3 模型不可用
- 確認 provider baseUrl / model id
- key 是否存在（但不要在 log/截圖中外流）

### 6.4 TLS/CA（企業網路常見）
症狀常見：
- `fetch failed`
- `UNABLE_TO_GET_ISSUER_CERT_LOCALLY`

處理方向（macOS）：
1) 匯出 System Roots：
```bash
security find-certificate -a -p /System/Library/Keychains/SystemRootCertificates.keychain > ~/.openclaw/certs/system-roots.pem
```
2) 設定 gateway 環境變數 `NODE_EXTRA_CA_CERTS=.../system-roots.pem`
3) 重啟 gateway

> 實際設定方式依你們部署（LaunchAgent/systemd）而不同；可在你們內部 runbook 補上標準作法。

---

## 7) 交付建議（給外部單位）

- 交付時請標註：
  - OpenClaw 版本
  - Node 版本
  - 使用的 model（OpenAI / NVIDIA Build）
- Secrets（API keys / tokens）：
  - 不入 git
  - 用環境變數 / tokenFile（權限 600）
  - Telegram 建議限制允許的 chat id
