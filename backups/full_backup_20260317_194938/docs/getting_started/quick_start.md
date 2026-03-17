# Quick Start（10 分鐘確認平台可用）

目標：確認 Charter 測試平台可正常運作。

---

## 前置設定

```bash
export CONTROL_PC_IP="172.14.1.140"
export CHARTER_BASE="http://${CONTROL_PC_IP}:5173"
```

---

## 1️⃣ 確認 UI 可開啟

- Web UI：`http://172.14.1.140:5173`

---

## 2️⃣ API 健康檢查

```bash
curl -fsSL "http://172.14.1.140:5173/api/health"
```

成功標準：回應 `{"ok": true}`

---

## 3️⃣ 確認 Worker 正常

```bash
curl -fsSL "http://172.14.1.140:5173/api/runs/worker/status"
```

成功標準：回應 `{"status": "idle"}` 或 `{"status": "running"}`

若不正常：
```bash
sudo systemctl status charter-worker.service
```

---

## 4️⃣ 查詢 Smoke 腳本 ID

在 Control PC 上執行：

```bash
curl -fsSL "http://172.14.1.140:5173/api/scripts?limit=2000" | python3 -c "
import json,sys
xs=json.load(sys.stdin)
want=['C00000004_NOC_API_basic_test','C00000001_SSH_basic_test','C00000003_WIFI_basic_test']
for name in want:
    hit=[s for s in xs if s.get('suite')=='sanity' and s.get('name')==name]
    if hit:
        print(f'{name}\tID={hit[0][\"id\"]}')
    else:
        print(f'{name}\tID=NOT_FOUND')
"
```

結果範例：
```
C00000004_NOC_API_basic_test	ID=5228
C00000001_SSH_basic_test	ID=5225
C00000003_WIFI_basic_test	ID=5227
```

---

## 5️⃣ 執行腳本

```bash
# 替換為實際 script_id
SCRIPT_ID=5225

curl -sS -X POST "http://172.14.1.140:5173/api/scripts/${SCRIPT_ID}/run"
```

會回傳 `run_id`（記下來）。

---

## 6️⃣ 查看執行結果

```bash
# 替換為實際 run_id
RID=<RUN_ID>

# 查看狀態
curl -fsSL "http://172.14.1.140:5173/api/runs/${RID}"

# 查看 log
curl -fsSL "http://172.14.1.140:5173/api/runs/${RID}/log" > run_${RID}_log.json
tail -n 30 run_${RID}_log.json
```

成功標準：`status=passed`，log 尾端顯示 `exit_code=0`

---

## 7️⃣ 清理（可選）

```bash
curl -sS -X DELETE "http://172.14.1.140:5173/api/runs/purge?older_than_days=0"
```

---

## 🔗 相關文件

- [Platform Links](/platform_links/) — 常用入口
- [Runs 操作](/user_guide/runs/) — 詳細說明
- [API Reference](/api_reference/)
