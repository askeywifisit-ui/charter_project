# Runs 操作

## 列出 runs
- `GET /api/runs?limit=200`

## 取得 log
- `GET /api/runs/{run_id}/log`

## Stop
- `POST /api/runs/{run_id}/stop`

## 清理（Purge）
- `DELETE /api/runs/purge?older_than_days=0`
  - 會刪已 finished 的 runs 與工作目錄

## 下載失敗 log archive
- `GET /api/runs/{run_id}/log-archives`
- `GET /api/runs/{run_id}/log-archive?name=...`
