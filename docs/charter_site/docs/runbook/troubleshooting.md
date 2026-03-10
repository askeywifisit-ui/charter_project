# 故障排除

## 1) UI 有開但 run 一直 queued
- 看 worker 是否 idle：`GET /api/runs/worker/status`

## 2) 脚本 fail 在 precondition：noc-context timeout
症狀常見：
- `HTTPSConnectionPool(...): Read timed out (read timeout=20)`

處理方向：
- 確認 Control PC 到 NOC endpoint 網路可達
- 增加 retry/backoff（腳本或 wrapper）
- 視情況拉長 timeout（避免尖峰時段 flakiness）

## 3) API set 成功但 CPE 端表未同步
- 屬 eventual consistency
- 用 wait/poll 等待 CPE reserved/leased table 出現再 assert
