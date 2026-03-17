# Common HTTP Status Codes & Troubleshooting

本頁整理 Charter API 常見的 HTTP status code 與對應原因/處置。

> 註：平台回應有時是 FastAPI 的預設格式（例如 `{"detail":"..."}`），有時是自訂 `{"ok":false,"error":"..."}`。

## 200 OK
- 意義：請求成功
- 注意：有些流程屬 **eventual consistency**（例如 cloud 設定寫入後，CPE 本地狀態更新需要時間），需要用 wait/poll 驗證。

## 400 Bad Request
- 常見原因：query/body 格式不符、缺必要欄位
- 處置：檢查 query string 與 JSON body；用 `jq` 產生 JSON 可降低手誤。

## 401 Unauthorized / 403 Forbidden
- Charter 平台通常在同源內網使用，這類錯誤較少出現。
- 若出現：通常是反向代理/驗證層或環境限制導致。

## 404 Not Found
- 常見原因：
  - script_id/run_id 不存在（已被刪除或 id 輸入錯）
  - 下載 archive 指定的 `name` 不存在
- 處置：
  - 用 `GET /api/scripts` 或 `GET /api/runs` 重新查 id
  - archive 先列出 `GET /api/runs/{rid}/log-archives`

## 405 Method Not Allowed
- 常見原因：用錯 HTTP method
  - 例如：`GET /api/runs/{rid}` 可能不支援（平台可能只支援 DELETE）
- 處置：對照 API 文件確認 method。

## 409 Conflict
- 常見原因：資源衝突（視平台實作；import 舊版可能會自動改名避免）
- 處置：依治理規範，建議「同名先刪再匯入」。

## 422 Unprocessable Entity
- 常見原因：FastAPI/Pydantic body 驗證失敗，或後端明確回報語意錯誤
  - 例如 DHCP reservation："This IP address is currently used by ..."
- 處置：
  - 檢查 body schema（欄位名/型別）
  - 針對可預期的 422（例如 IP in use），腳本端加入 retry/換 IP 策略

## 5xx（500/502/503/504）
- 常見原因：worker/API 服務異常、上游依賴（NOC endpoint）不穩、超時
- 處置：
  - 先看 `GET /api/runs/worker/status` 是否卡住
  - 若是 `noc-context timeout`：增加 retry/backoff、拉長 timeout，並確認 control PC 出口網路/ DNS

## 建議的除錯手法（最實用）
- 用 `-i` 看 response headers/status：
```bash
curl -sS -i "$CHARTER_BASE/api/health" | head -n 30
```
- 對 JSON 回應加 `| jq .` 方便閱讀
- 需要下載檔案（zip/gzip）用 `-o` 存檔，不要直接印在 terminal
