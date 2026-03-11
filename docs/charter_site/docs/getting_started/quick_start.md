# Quick Start（10 分鐘確認平台可用）

目標：用最短步驟確認你可以 **打開 UI → API 可用 → worker 正常 → 跑一個 sanity → 抓 log**。

> 只要這頁跑通，後面所有 test case 才有意義。

---

## 0) 先填三個變數（建議直接照這個填）

!!! tip "建議範例（11 LAB）"

    ```bash
    export CONTROL_PC_IP="172.14.1.140"
    export CHARTER_BASE="http://${CONTROL_PC_IP}:5173"
    # 最穩的 smoke（擇一）：
    export SCRIPT_ID="<fill>"  # 例如 C00000001_SSH_basic_test 的 11F_140 script id
    ```

> `SCRIPT_ID` 建議用「最小 smoke case」；不要一開始就跑會 power-cycle 的 case。

---

## 1) 開 UI（人工確認）

- UI：`http://<CONTROL_PC_IP>:5173`
- 你應該看得到：Scripts / Runs / Suites 等頁面

---

## 2) API 健康檢查

```bash
curl -fsSL "${CHARTER_BASE}/api/health" | python3 -m json.tool
```

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

## 4) 列出 scripts（找 script_id）

### 4.1 直接列出（大量）
```bash
curl -fsSL "${CHARTER_BASE}/api/scripts?limit=2000" | python3 -m json.tool | head
```

### 4.2 只找 smoke case（推薦）
```bash
curl -fsSL "${CHARTER_BASE}/api/scripts?limit=2000" \
  | python3 - <<'PY'
import json,sys
xs=json.load(sys.stdin)
want={'C00000001_SSH_basic_test','C00000003_WIFI_basic_test'}
for s in xs:
    if s.get('suite')=='sanity' and s.get('name') in want:
        print(f"{s.get('name')}\tID={s.get('id')}")
PY
```

---

## 5) 觸發 run

```bash
curl -sS -X POST "${CHARTER_BASE}/api/scripts/${SCRIPT_ID}/run" | python3 -m json.tool
```

回傳會有 `run_id`（以下用 `RID`）。

> 若回傳一直卡住或沒有 run_id：優先檢查 worker status。

---

## 6) 看 run log / artifacts

```bash
RID=<RUN_ID>

curl -sS "${CHARTER_BASE}/api/runs/${RID}/log" > run_${RID}_log.json
cat run_${RID}_log.json | head

# 若有 log archive
curl -sS "${CHARTER_BASE}/api/runs/${RID}/log-archives" | python3 -m json.tool
curl -fsSL "${CHARTER_BASE}/api/runs/${RID}/log-archive" -o run_${RID}_cpe_log.tar.gz
```

---

## 7) 清理（建議日常都做）

```bash
curl -sS -X DELETE "${CHARTER_BASE}/api/runs/purge?older_than_days=0" | python3 -m json.tool
```
