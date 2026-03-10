# Quick Start

## 目標
用最短步驟確認你可以：
1) 打開 UI
2) 列出 scripts
3) 觸發 run 並查看 log

## 1) 開 UI
- `http://{{CONTROL_PC_IP}}:5173`

## 2) Scripts
- UI：`/scripts` 或 `/suites`
- API：`GET /api/scripts`

## 3) 跑一個 script
- API：`POST /api/scripts/{script_id}/run`
- UI：Scripts 頁面點 Run

## 4) 看 run log
- API：`GET /api/runs/{run_id}/log`

> 若 worker 卡住：看 `GET /api/runs/worker/status` 或 UI 的 worker 狀態。
