# Runs 操作（Queue / Log / Evidence / Cleanup）

> 入口（同事照做版）：[腳本修改 SOP（Export → Modify → Import → Run → Evidence）](script_change_sop.md)

本頁定位：Runs 的「操作 + 排錯」速查。

---

## TL;DR（最常用 4 件事）

1) 找到最新 run：`GET /api/runs?limit=...`
2) 抓 log 當 evidence：`GET /api/runs/<rid>/log`
3) fail 時抓 log archive（若有）：`/log-archives` + `/log-archive`
4) 定期 purge（避免磁碟塞滿）：`DELETE /api/runs/purge?older_than_days=0`

---

## 0) 先設定 base

```bash
export CONTROL_PC_IP="<fill>"   # 例：172.14.1.140
export CHARTER_BASE="http://${CONTROL_PC_IP}:5173"
```

---

## 1) 列出 runs（找 RID）

```bash
curl -fsSL "$CHARTER_BASE/api/runs?limit=50" | python3 -m json.tool
```

### 1.1 只列出最近 N 筆的 rid（快速）

```bash
curl -fsSL "$CHARTER_BASE/api/runs?limit=50" \
  | python3 - <<'PY'
import json,sys
xs=json.load(sys.stdin)
for r in xs[:20]:
    print('rid=', r.get('id'), 'status=', r.get('status'), 'script_id=', r.get('script_id'))
PY
```

---

## 2) 抓 log（Evidence）

```bash
RID=<RUN_ID>

curl -sS "$CHARTER_BASE/api/runs/$RID/log" > run_${RID}_log.json
ls -lh run_${RID}_log.json
```

> 建議：對外/跨單位回報時，先附上 `run_<RID>_log.json`。

---

## 3) Stop（中止執行中的 run）

```bash
RID=<RUN_ID>
curl -sS -X POST "$CHARTER_BASE/api/runs/$RID/stop" | python3 -m json.tool
```

---

## 4) 下載失敗 log archive（若有）

> 用途：腳本 fail 時，worker 可能會自動打包 CPE logs。這是最常用的第二份 evidence。

```bash
RID=<RUN_ID>

curl -sS "$CHARTER_BASE/api/runs/$RID/log-archives" | python3 -m json.tool

# 若回傳顯示有 archive，可直接下載（預設會拿「主要那份」）
curl -fsSL "$CHARTER_BASE/api/runs/$RID/log-archive" -o run_${RID}_cpe_log.tar.gz
ls -lh run_${RID}_cpe_log.tar.gz
```

---

## 5) Worker 狀態（queued 卡住先看這個）

```bash
curl -fsSL "$CHARTER_BASE/api/runs/worker/status" | python3 -m json.tool
```

若 worker 不正常：
```bash
sudo systemctl status charter-worker.service --no-pager
sudo journalctl -u charter-worker.service -n 200 --no-pager
```

---

## 6) 清理（Purge）

> 會刪已 finished 的 runs 與工作目錄（避免磁碟被塞滿）。

```bash
curl -sS -X DELETE "$CHARTER_BASE/api/runs/purge?older_than_days=0" | python3 -m json.tool
```

---

## 7) 常見問題（FAQ）

### Q1：為什麼 run 一直 queued？
A：先看 worker status（上一節），再看 `charter-worker.service` log。

### Q2：log-archive 下載不到？
A：先看 `/log-archives` 是否有列出 archive，沒有代表腳本沒有產出該 evidence。
