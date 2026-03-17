# Cycles 調整（OpenClaw 測試助理：單次 / 批次）

本頁說明如何在跑 **sanity / stability** 之前，快速調整腳本的 `CYCLES` / `CYCLE_INTERVAL`（或 `INTERVAL`）等「迴圈/間隔」設定。

> 重點：stability 常用來做長跑，但平台上有些腳本可能預設 `CYCLES=1`（方便冒煙）。正式長跑前請先調整。

---

## A) 用 OpenClaw 測試助理（建議）

### 你要提供什麼資訊

你只要用自然語言告訴測試助理：

- suite：`sanity` 或 `stability`
- 目標：
  - 單支：指定 script name（或 script_id）
  - 批次：整個 suite（或用 name 關鍵字篩選）
- 你要改的值：
  - `CYCLES`（跑幾輪）
  - `CYCLE_INTERVAL`（每輪等待秒數；部分腳本可能用 `INTERVAL`）
- 是否要「跑完改回來」（是/否）

**範例（單次）**
- 「把 stability 的 `A2435635_Continuously_executing_speedtest` 改成 `CYCLES=200`、`CYCLE_INTERVAL=90`，改完立刻跑 1 次。」

**範例（批次）**
- 「把 stability 全部腳本都改成 `CYCLES=100`、`CYCLE_INTERVAL=60`，IPv6 相關跳過。」

### 測試助理會怎麼做（概念）

1. 先用 API 列出 scripts：`GET /api/scripts?suite=...`
2. 讀每支的 manifest：`GET /api/scripts/{id}/manifest`
3. 只改 manifest 內的 `env.CYCLES` / `env.CYCLE_INTERVAL`（或 `env.INTERVAL`）
4. 用 API 回寫：`PUT /api/scripts/{id}/manifest`
5. （可選）幫你觸發 run：`POST /api/scripts/{id}/run`

---

## B) 手動（不靠助理，照步驟做）

> 本節給維運/整合人員用：想用 curl 直接改 manifest。

### 1) 設定 base

```bash
export CHARTER_BASE="http://{{CONTROL_PC_IP}}:5173"
```

### 2) 找到 script_id

用名稱查（建議，避免 script_id 變動）：

```bash
curl -sS "$CHARTER_BASE/api/scripts?suite=stability&q=A2435635" | python3 -m json.tool
```

從輸出找到 `id`。

### 3) 讀取 manifest

```bash
SCRIPT_ID=5059
curl -sS "$CHARTER_BASE/api/scripts/$SCRIPT_ID/manifest" | python3 -m json.tool > manifest_${SCRIPT_ID}.json
```

`content` 欄位就是 YAML 文字。

### 4) 修改 YAML（建議先備份）

把 `env:` 區塊內的：

- `CYCLES: '1'` → `CYCLES: '200'`
- `CYCLE_INTERVAL: '90'`（或 `CYCLE_INTERVAL: 90`）改成你要的值

> 注意：有些腳本使用 `INTERVAL`；請以該腳本 manifest 為準。

### 5) 回寫 manifest

把更新後的 YAML 當成 JSON body 的 `content` 送回去：

```bash
python3 - <<'PY'
import json
content=open('manifest.yaml','r',encoding='utf-8').read()
print(json.dumps({'content': content}, ensure_ascii=False))
PY > put_manifest.json

curl -sS -X PUT "$CHARTER_BASE/api/scripts/$SCRIPT_ID/manifest" \
  -H 'Content-Type: application/json' \
  --data-binary @put_manifest.json | python3 -m json.tool
```

---

## C) 常見注意事項

- **先決定你要改的是 cycles 還是 interval**：
  - cycles：跑幾輪
  - interval：每輪之間等待
- **批次修改前先說清楚排除條件**：例如 IPv6 相關不跑、或某些高風險 case（Factory reset / power-cycle）要另外確認。
- **跑完要不要改回來**：建議在 longrun 結束後改回 `CYCLES=1`，避免下次不小心跑很久。

---

## D) 相關連結

- [Test Suites → Sanity](/test_suites/sanity/)
- [Test Suites → Stability](/test_suites/stability/)
- [Environment Template（換環境必讀）](/environment_template/)
