# Quick Start（10 分鐘確認平台可用）

目標：用最短步驟確認你可以 **打開 UI → API 可用 → worker 正常 → 跑一個 sanity → 抓 log**。

> 只要這頁跑通，後面所有 test case 才有意義。

---

## 0) 先填三個變數

```bash
export CONTROL_PC_IP="<CONTROL_PC_IP>"   # 例如 172.14.1.140
export CHARTER_BASE="http://${CONTROL_PC_IP}:5173"
export SCRIPT_ID="<SCRIPT_ID_11F_140>"   # 選一個簡單的 sanity，例如 SSH basic
```

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

---

## 4) 列出 scripts（找 script_id）

```bash
curl -fsSL "${CHARTER_BASE}/api/scripts?limit=2000" | python3 -m json.tool | head
```

---

## 5) 觸發 run

```bash
curl -sS -X POST "${CHARTER_BASE}/api/scripts/${SCRIPT_ID}/run" | python3 -m json.tool
```

回傳會有 `run_id`（以下用 `RID`）。

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
