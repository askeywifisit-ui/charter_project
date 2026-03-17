# cpe_info

- 位置（control PC）：`/home/da40/charter/tools/cpe_info`
- 類型：可執行檔

## Overview
`cpe_info` 用來**快速取得 DUT/CPE 的關鍵狀態**，常用於：
- boot 後 ready gate（Internet/Cloud 是否 Connected）
- 取得 `node-id`（供 NOC API 查 location、做 ssh-enable 等）
- 取得 console password（某些腳本需要）

此工具會被：
- scripts（sanity/stability）
- 平台 API（例如 `/api/cpe/info`）
直接依賴，因此屬於 **runtime 必備**。

## 常用命令（建議照抄）
### 1) 狀態（ready gate）
```bash
/home/da40/charter/tools/cpe_info --status
```

### 2) Internet / Cloud
```bash
/home/da40/charter/tools/cpe_info --internet
```

### 3) node id
```bash
/home/da40/charter/tools/cpe_info --node-id
```

### 4) console password（若需要）
```bash
/home/da40/charter/tools/cpe_info --password
```

## 常見輸出（關鍵字）
- `Internet Status: Connected`
- `Cloud Status: Connected`

## 常見問題 / 排除
- boot 過程常見短暫訊息（屬正常）：
  - `ERROR: cannot fetch index.cgi`
  - `Internet Status: Determining...`
  - `Cloud Status: Not Connected`
  建議用 retry（例如每 3 秒重試 10~60 次）而不是一次就判 fail。
