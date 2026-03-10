# NOC Profile / Secrets 設定（交付外部單位必讀）

本頁說明 Charter 平台與 scripts 常用的 NOC/Cloud 設定來源（profiles/secrets），以及交付外部單位時需要準備哪些資訊。

> **安全原則**：secrets 不進 git、不貼到群組；以檔案/密碼管理器安全交付。

---

## 本環境參考值（11 LAB）

> 注意：本頁只放「路徑/欄位/命名」，不放任何 email/password。

- NOC base（例）：`https://piranha-int.tau.dev-charter.net`
- profiles 檔位置（11F_140 / 11F_131 一致）：
  - `PROFILES_FILE=/home/da40/charter/.secrets/noc_profiles.json`
- profile 名稱（例）：
  - `NOC_PROFILE=SPECTRUM_INT`
- customer id（例）：
  - `CUSTOMER_ID=682d4e5179b80027cd6fb27e`

> 交付外部單位時，以上 4 項通常都需要替換/重新取得。

## 1) 主要設定檔：`noc_profiles.json`

> **交付提醒（必讀）**：
> - `noc_profiles.json` 是「每個單位/客戶都必須自行填寫」的 secrets 檔案（base URL / email / password）。
> - **不要**把 CSIT/實驗室的 `noc_profiles.json` 原檔直接交付給客戶（可能含內網 endpoint 與帳密）。
> - 交付時請提供 `noc_profiles.template.json`（範本），由客戶依其環境填入。

### 路徑（本環境）
- `PROFILES_FILE=/home/da40/charter/.secrets/noc_profiles.json`

### 使用方式（scripts 常見）
- 指定：
  - `NOC_PROFILE={{NOC_PROFILE}}`（例：`SPECTRUM_INT`）
  - `PROFILES_FILE={{PROFILES_FILE}}`
- 腳本會從 profiles 檔取出：
  - `base`（NOC API base URL）
  - `email`
  - `password`

### 檔案格式（示意）
```json
{
  "SPECTRUM_INT": {
    "base": "https://piranha-int.tau.dev-charter.net",
    "email": "user@example.com",
    "password": "***"
  }
}
```

> profile key 通常不分大小寫（腳本多會做 upper/lower 相容），但建議固定用同一種。

---

## 2) 必填 ID：`CUSTOMER_ID`
### 來源
- 多數 NOC API 需要 `customer_id` 來查 location / 執行 ssh_enable / speedtest / dhcp reservation。

### 常見設定（manifest env）
```yaml
CUSTOMER_ID: "{{CUSTOMER_ID}}"
NOC_PROFILE: "{{NOC_PROFILE}}"
PROFILES_FILE: "{{PROFILES_FILE}}"
```

---

## 3) 如何快速驗證 secrets 是否可用
> 建議交付外部單位先做以下驗證，避免跑腳本才發現 `noc-context timeout`。

### (A) 從 control PC 測試 NOC endpoint 可達
```bash
# DNS/路由要通
curl -sS -I https://piranha-int.tau.dev-charter.net | head
```

### (B) 用腳本最小流程驗證（建議跑一條會 login 的 sanity/stability）
- 例如跑：`C00000001_SSH_basic_test` 或 `A2435635_Continuously_executing_speedtest`

並觀察 run log 是否出現：
- `noc-profile-applied`
- `step: login ok: true`
- `location-id ...`

---

## 4) 常見失敗與排除
### `noc-context timeout`
- 症狀：
  - `HTTPSConnectionPool(...): Read timed out (read timeout=20)`
- 常見原因：
  - NOC endpoint 當下慢/不穩
  - control PC 出口網路/DNS/Proxy 設定問題
- 建議處理：
  - 對 NOC context 加 retry/backoff（我們已在部分腳本 wrapper 做過）
  - 拉長 timeout（若可接受執行時間變長）
  - 確認 control PC 到 NOC endpoint 的路由/防火牆

---

## 5) 交付外部單位清單（你要提供什麼）
- `noc_profiles.json`（或讓對方自行建立）
- `CUSTOMER_ID`
- 指定要用的 `NOC_PROFILE` 名稱
- 若有多環境（INT/UAT/PROD），請明確標註每個 profile 對應用途
