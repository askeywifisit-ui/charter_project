# Quick Start（10 分鐘確認平台可用）

目標：用最短步驟確認你可以 **打開 UI → API 可用 → worker 正常 → 跑一個 smoke/sanity → 抓 log（可取證）**。

> 只要這頁跑通，後面所有 test case 才有意義。

本頁設計原則：**API 優先**（UI 只做人工確認/觀察）。

---

## 0) 先填兩個變數（建議直接照這個填）

!!! tip "建議範例（11 LAB）"

    ```bash
    export CONTROL_PC_IP="172.14.1.140"
    export CHARTER_BASE="http://${CONTROL_PC_IP}:5173"
    ```

> 這頁不建議你手填 `SCRIPT_ID`。**用名稱查回 script_id** 比較穩（script_id 會因 delete/import 變動）。

---

## 1) 開 UI（人工確認）

- UI：`http://<CONTROL_PC_IP>:5173`
- 你應該看得到：Scripts / Runs / Suites 等頁面

---

## 2) API 健康檢查

```bash
curl -fsSL "${CHARTER_BASE}/api/health" | python3 -m json.tool
```

成功標準：回應包含 `{"ok": true}`。

---

## 3) Worker 狀態（最常卡住的點）

```bash
curl -fsSL "${CHARTER_BASE}/api/runs/worker/status" | python3 -m json.tool
```

若 worker 不正常：先看 `systemctl status charter-worker.service`。

常用 log：
```bash
sudo journalctl -u charter-worker.service -n 200 --no-pager
```

---

## 4) 列出 scripts（用名稱查 script_id）

### 4.1 直接列出（大量）
```bash
curl -fsSL "${CHARTER_BASE}/api/scripts?limit=2000" | python3 -m json.tool | head
```

### 4.2 只找 smoke case（推薦）

> 建議 demo/驗證順序：先跑 **NOC API basic** 或 **SSH basic**；Wi‑Fi 類 smoke 再跑。

```bash
curl -fsSL "${CHARTER_BASE}/api/scripts?limit=2000" \
  | python3 - <<'PY'
import json,sys
xs=json.load(sys.stdin)
want=[
  'C00000004_NOC_API_basic_test',
  'C00000001_SSH_basic_test',
  'C00000003_WIFI_basic_test',
]
for name in want:
    hit=[s for s in xs if s.get('suite')=='sanity' and s.get('name')==name]
    if hit:
        s=hit[0]
        print(f"{name}\tID={s.get('id')}")
    else:
        print(f"{name}\tID=<NOT_FOUND>")
PY
```

把你要跑的那支 script_id 記下來：
```bash
SCRIPT_ID=<FILL>
```

---

## 5) 觸發 run

```bash
curl -sS -X POST "${CHARTER_BASE}/api/scripts/${SCRIPT_ID}/run" | python3 -m json.tool
```

回傳會有 `run_id`（以下用 `RID`）。

> 若回傳一直卡住或沒有 run_id：優先檢查 worker status。

### 5.1 等待 run 結束（不用 UI）

```bash
RID=<RUN_ID>

# 看最新 runs（找到 RID 的 status=queued/running/passed/failed）
curl -sS "${CHARTER_BASE}/api/runs?limit=50" | python3 -m json.tool
```

---

## 6) 看 run log / artifacts（取證）

```bash
RID=<RUN_ID>

curl -sS "${CHARTER_BASE}/api/runs/${RID}/log" > run_${RID}_log.json
# log 是一行一個 event（多半是 JSON 字串）；先看 tail 最快
tail -n 30 run_${RID}_log.json

# 若有 log archive（通常是 fail-hook 抓到的 CPE logpull）
curl -sS "${CHARTER_BASE}/api/runs/${RID}/log-archives" | python3 -m json.tool
curl -fsSL "${CHARTER_BASE}/api/runs/${RID}/log-archive" -o run_${RID}_cpe_log.tar.gz
```

成功標準（快速判斷）：
- `run status=passed`
- log 尾端可看到類似：`[runner] exit_code=0`

---

## 7) 清理（建議日常都做）

```bash
curl -sS -X DELETE "${CHARTER_BASE}/api/runs/purge?older_than_days=0" | python3 -m json.tool
```
