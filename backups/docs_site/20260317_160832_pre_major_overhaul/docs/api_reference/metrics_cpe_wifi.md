# Dashboard / Metrics / Wi‑Fi / CPE

## GET `/api/dashboard/metrics`
- 用途：Dashboard 圖表與 pass rate、events

### curl
```bash
curl -sS "$CHARTER_BASE/api/dashboard/metrics?window_hours=24&events=eventlog" | jq .
```
- Query（v3 版本）：
  - `window_hours: int`（預設 24；1~720）
  - `limit_events: int`（預設 200；1~1000）
  - `events: eventlog|runs|both`（預設 eventlog）
- 回應欄位：
  - `source`
  - `pass_rate`：`{"stability":..,"sanity":..,"regression":..}`
  - `cpu/mem/temp/throughput/throughput_dl/throughput_ul/latency`：`[{"ts":"...","value":...}, ...]`
  - `events`：`[{"ts":"...","msg":"..."}, ...]`
  - debug：`ev1_count/ev2_count/ev2_fallback_used/dl_count/ul_count`

## POST `/api/metrics/push`
- 用途：agent push 指標（含 wifi_clients / wifi_bands / radio）

### curl
最小送一筆：
```bash
jq -n '{cpu_pct:10, mem_pct:20, temp_c:45, rx_mbps:100, tx_mbps:50, latency_ms:12}' \
  | curl -sS -X POST "$CHARTER_BASE/api/metrics/push" \
      -H 'Content-Type: application/json' \
      -d @- | jq .
```
- Body：JSON（鍵名支援舊名相容）
  - cpu: `cpu_pct|cpu`
  - mem: `mem_pct|mem`
  - temp: `temp_c|tmp`
  - rx/tx: `rx_mbps|rx`, `tx_mbps|tx`
  - latency: `latency_ms|lat`
  - run id: `run_id|rid`
  - `wifi_clients`（可選）
  - `wifi_bands` 或 `wifi_clients_per_band`（可選，dict）
  - `radio`（可選，list of dict）
- 回應：`{"ok": true}`

## GET `/api/metrics/latest`
- 用途：取最新 N 筆 metrics

### curl
```bash
curl -sS "$CHARTER_BASE/api/metrics/latest?n=10" | jq .
```
- Query：
  - `n`（預設 60；1~600）
  - `limit`（可選；若給則覆蓋 n）
- 回應：
  ```json
  {"ok": true, "data": [{"ts":"...","cpu_pct":.., "wifi_bands": ...}, ...]}
  ```

## 其他 metrics 相關（舊路徑/維運用）
- `GET /api/metrics/age`
- `GET /api/metrics/latest_sanitized`
- `GET /api/metrics/debug`
- `GET /api/metrics/suite_pass_rate`
- `GET /api/metrics/dashboard`
- `GET /api/metrics/cpe/info`

## Wi‑Fi
- `GET /api/wifi/stations/count`：回報最新 wifi_clients
- `GET /api/wifi/radio/state`：回報最新一組 wifi_radio_state

### curl
```bash
curl -sS "$CHARTER_BASE/api/wifi/stations/count" | jq .
curl -sS "$CHARTER_BASE/api/wifi/radio/state" | jq .
```

## CPE
- `GET /api/cpe/status/latest`：CPE status（stale gate 用）
- `GET /api/cpe/info_cached`：快取版 CPE info
- `GET /api/cpe/info`：執行 `CPE_INFO_CMD`（預設 `/home/da40/charter/tools/cpe_info`）解析輸出
  - 成功：`{"ok": true, "data": {...}, "raw": "...", "code": 0}`

### curl
```bash
curl -sS "$CHARTER_BASE/api/cpe/status/latest" | jq .
curl -sS "$CHARTER_BASE/api/cpe/info_cached" | jq .
curl -sS "$CHARTER_BASE/api/cpe/info" | jq .
```

## Event Log
- `POST /api/event-log/clear`：清 event_log（Dashboard 頁有用到）

### curl
```bash
curl -sS -X POST "$CHARTER_BASE/api/event-log/clear" | jq .
```
