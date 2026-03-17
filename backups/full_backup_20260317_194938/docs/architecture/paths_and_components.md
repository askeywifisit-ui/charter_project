# Platform Paths & Components

## Control PC（目前環境：172.14.1.140）主要路徑
- tools：`/home/da40/charter/tools`
- web：`/home/da40/charter/apps/web`
- api：`/home/da40/charter/apps/api/app/`
- data：`/home/da40/charter/data`
  - `scripts/`：上傳的 zip
  - `work/run_<id>/`：每次 run 的工作目錄
  - `venv/script_<script_id>/`：每支 script 的 venv

## 元件關係（簡述）
- Web UI（5173）同源呼叫 `/api/...`
- API（FastAPI）提供 scripts/runs/worker 等管理介面
- Worker 從 queue 取 run，解壓 zip → 建 venv → 執行 entrypoint
- Fail-hook 會做 logpull（視工具/腳本設定）

> 交付其他單位時，路徑與網卡介面替換規則請見 Environment Template。
