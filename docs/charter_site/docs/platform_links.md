# Platform Links（平台入口）

本頁提供「目前運作中的 Charter 平台」常用入口，讓讀者可以從文件直接跳到 UI / API。

## 本環境參考值（lab）
- Control PC：`172.14.1.140`
- UI Base：`http://172.14.1.140:5173`
- API Base：`http://172.14.1.140:5173/api`

> 交付外部單位時，請將 `172.14.1.140` 替換為對方的 control PC IP（見 Environment Template）。

---

## A) Web UI（給操作人員）
- UI Home：`http://{{CONTROL_PC_IP}}:5173/`
- Scripts：`http://{{CONTROL_PC_IP}}:5173/scripts`
- Suites：`http://{{CONTROL_PC_IP}}:5173/suites`
- Runs：`http://{{CONTROL_PC_IP}}:5173/runs`

> 若你不確定 UI 路由名稱，最保險是先開 Home 再從左側選單進入。

---

## B) API（給整合/維運）
- Health：`http://{{CONTROL_PC_IP}}:5173/api/health`
- Scripts list：`http://{{CONTROL_PC_IP}}:5173/api/scripts`
- Runs list：`http://{{CONTROL_PC_IP}}:5173/api/runs`
- Worker status：`http://{{CONTROL_PC_IP}}:5173/api/runs/worker/status`
- Dashboard metrics：`http://{{CONTROL_PC_IP}}:5173/api/dashboard/metrics`

---

## C) 常見工作流（從 link 到實際操作）

下面把「匯入 → 執行 → 取證 → 清理」寫成可以照做的步驟。

### 0) 先設定 base（只做一次）
```bash
export CHARTER_BASE="http://{{CONTROL_PC_IP}}:5173"
```

### 1) 匯入腳本（import2）
把 zip 匯入到指定 suite（例：sanity）：
```bash
curl -sS -X POST "$CHARTER_BASE/api/scripts/import2" \
  -F 'suite=sanity' \
  -F 'file=@./your_script.zip;type=application/zip' | jq .
```

### 2) 查 script_id（用腳本名稱/關鍵字查）
```bash
curl -sS "$CHARTER_BASE/api/scripts?suite=sanity&q=YourScriptName" | jq .
```
找到輸出中的 `id`，把它記下來：
```bash
SCRIPT_ID=123
```

### 3) Run（執行）
```bash
curl -sS -X POST "$CHARTER_BASE/api/scripts/$SCRIPT_ID/run" | jq .
```
回應會包含 `run_id`，把它記下來：
```bash
RID=1234
```

### 4) 拉 log（最重要的證據）
```bash
curl -sS "$CHARTER_BASE/api/runs/$RID/log" > run_${RID}_log.json
# 快速看最後 50 行
#（log 可能是 JSON array 或單一字串，先 tail 看即可）
tail -n 50 run_${RID}_log.json
```

### 5) 下載 archive（只在 fail-hook 有產生時才會有）
先列出有哪些檔：
```bash
curl -sS "$CHARTER_BASE/api/runs/$RID/log-archives" | jq .
```
下載最新一份：
```bash
curl -fsSL "$CHARTER_BASE/api/runs/$RID/log-archive" -o run_${RID}_cpe_log.tar.gz
```

### 6) purge（清理已完成的 runs + workdir，避免磁碟爆）
```bash
curl -sS -X DELETE "$CHARTER_BASE/api/runs/purge?older_than_days=0" | jq .
```

> 詳細版請見：`API Reference → Workflows（實戰）`

---
