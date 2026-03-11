# Runs 操作

> 入口（同事照做版）：[腳本修改 SOP（Export → Modify → Import → Run → Evidence）](script_change_sop.md)

本頁是 Runs API 的速查表（適合貼在終端機旁）。

---

## 1) 列出 runs

```bash
curl -fsSL "$CHARTER_BASE/api/runs?limit=200" | python3 -m json.tool | head
```

---

## 2) 取得 log

```bash
RID=<RUN_ID>
curl -sS "$CHARTER_BASE/api/runs/$RID/log" > run_${RID}_log.json
```

---

## 3) Stop（中止執行中的 run）

```bash
RID=<RUN_ID>
curl -sS -X POST "$CHARTER_BASE/api/runs/$RID/stop" | python3 -m json.tool
```

---

## 4) 下載失敗 log archive（若有）

```bash
RID=<RUN_ID>

curl -sS "$CHARTER_BASE/api/runs/$RID/log-archives" | python3 -m json.tool
curl -fsSL "$CHARTER_BASE/api/runs/$RID/log-archive" -o run_${RID}_cpe_log.tar.gz
```

---

## 5) 清理（Purge）

> 會刪已 finished 的 runs 與工作目錄（避免磁碟被塞滿）。

```bash
curl -sS -X DELETE "$CHARTER_BASE/api/runs/purge?older_than_days=0" | python3 -m json.tool
```
