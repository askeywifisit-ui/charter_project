# 常用維運

## 檢查 worker 狀態
- `GET /api/runs/worker/status`

## 清理 runs/workdir
- `DELETE /api/runs/purge?older_than_days=0`

## 常見資料位置（Control PC）
- workdir：`/home/da40/charter/data/work/run_<id>/`
- venv：`/home/da40/charter/data/venv/script_<script_id>/`

## 變更前規範
- 任何改動前：先備份腳本與程式碼
- 匯入前：同名（suite+name）先刪再匯入
