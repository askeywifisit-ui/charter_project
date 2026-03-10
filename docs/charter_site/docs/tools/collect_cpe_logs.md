# collect_cpe_logs.py

- 位置（control PC）：`/home/da40/charter/tools/collect_cpe_logs.py`

## Overview
`collect_cpe_logs.py` 是 worker 的共用 fail-hook：當 run 失敗時，嘗試從 CPE 端把 logpull 壓縮檔抓回來，存到 run 工作目錄，並讓 UI/API 可以下載。

此工具通常會：
1) 先做 TCP port 22 檢查（SSH 是否開）
2) 必要時嘗試 cloud ssh-enable（若 `USE_CLOUD_SSH=1` 且 env 齊全）
3) 呼叫 `cpe_ssh.py --cmd pull-log` 下載 tar.gz
4) 產生結構化 JSON log（GUI 好讀）

## 你會在哪裡看到結果
### A) run 工作目錄（control PC）
- `/home/da40/charter/data/work/run_<RID>/cpe_log/`

### B) 透過平台 API
- 列出：`GET /api/runs/<RID>/log-archives`
- 下載：`GET /api/runs/<RID>/log-archive`

## 常見問題 / 排除
- SSH 沒開：需要先 NOC enable SSH，且 boot 後 port 22 可能延遲
- 權限/密碼：優先讀環境變數 `SSH_USER/SSH_PASSWORD` 或 `CPE_USER/CPE_PASSWORD`

> 建議：交付外部單位時，把「logpull 產物路徑」與「下載 API」寫進 runbook。
