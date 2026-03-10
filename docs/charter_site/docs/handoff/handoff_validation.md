# 驗證步驟（快速驗證 / 同事照做版）

目標：對方在替換環境後，快速確認平台可用（**API/worker/scripts/run/log**）。

---

## 0) 設定 base

```bash
export CONTROL_PC_IP="<CONTROL_PC_IP>"
export CHARTER_BASE="http://${CONTROL_PC_IP}:5173"
```

---

## 1) API health

```bash
curl -fsSL "$CHARTER_BASE/api/health" | python3 -m json.tool
```

---

## 2) Worker health（最重要）

```bash
curl -fsSL "$CHARTER_BASE/api/runs/worker/status" | python3 -m json.tool
```

若這一步不正常，先看：
```bash
sudo systemctl status charter-worker.service --no-pager
```

---

## 3) Scripts（確認資料存在）

```bash
curl -fsSL "$CHARTER_BASE/api/scripts?limit=2000" | python3 -m json.tool | head
```

---

## 4) Run 一條最小 sanity

建議選一條最穩的 smoke（例如 `C00000001_SSH_basic_test` 或 `C00000003_WIFI_basic_test`）。

1) 先找 script_id：
```bash
curl -fsSL "$CHARTER_BASE/api/scripts?limit=2000" \
  | python3 - <<'PY'
import json,sys
xs=json.load(sys.stdin)
# 改成你要的 name
name='C00000001_SSH_basic_test'
for s in xs:
    if s.get('name')==name and s.get('suite')=='sanity':
        print('SCRIPT_ID=', s.get('id'))
        break
PY
```

2) 執行：
```bash
SCRIPT_ID=<SCRIPT_ID>
curl -sS -X POST "$CHARTER_BASE/api/scripts/$SCRIPT_ID/run" | python3 -m json.tool
```

3) 取 log：
```bash
RID=<RUN_ID>
curl -sS "$CHARTER_BASE/api/runs/$RID/log" > run_${RID}_log.json
```

---

## 5) 失敗時：下載 log archive（若有）

```bash
RID=<RUN_ID>
curl -sS "$CHARTER_BASE/api/runs/$RID/log-archives" | python3 -m json.tool
curl -fsSL "$CHARTER_BASE/api/runs/$RID/log-archive" -o run_${RID}_cpe_log.tar.gz
```

---

## 6) 清理 runs/workdir（建議）

```bash
curl -sS -X DELETE "$CHARTER_BASE/api/runs/purge?older_than_days=0" | python3 -m json.tool
```
