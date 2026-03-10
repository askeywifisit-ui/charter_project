# Modify Script Code（修改 zip 內 Python 程式碼的標準流程）

平台目前提供的「可直接修改」能力主要是 **manifest**（`PUT /api/scripts/{id}/manifest`）。

若要修改 zip 內的 Python 程式碼（例如 `main_impl.py` / `cycle_wrapper.py`），建議採用以下標準流程：

> 原則（DA40 規範）：任何改動前先備份；匯入前「同名先刪再匯入」避免 DUPLICATE。

---

## 0) 先設定 base
```bash
export CHARTER_BASE="http://{{CONTROL_PC_IP}}:5173"
```

---

## 1) 找到 script_id（用名稱查）
```bash
NAME='YourScriptName'
curl -sS "$CHARTER_BASE/api/scripts?suite=sanity&q=$NAME" | jq .
```
把 `id` 記下來：
```bash
SCRIPT_ID=123
SUITE=sanity
```

---

## 2) Export zip（先備份）
```bash
mkdir -p backup_scripts
curl -fsSL "$CHARTER_BASE/api/scripts/$SCRIPT_ID/export" -o "backup_scripts/${NAME}_${SCRIPT_ID}.zip"
```

---

## 3) 解壓 → 修改程式碼 → 重新打包
```bash
WORKDIR="work_${NAME}_${SCRIPT_ID}"
rm -rf "$WORKDIR" && mkdir -p "$WORKDIR"
unzip -q "backup_scripts/${NAME}_${SCRIPT_ID}.zip" -d "$WORKDIR"

# 這裡用你習慣的編輯器修改，例如：
# vi "$WORKDIR/main_impl.py"
# vi "$WORKDIR/cycle_wrapper.py"

# 修改完重新打包
( cd "$WORKDIR" && zip -qr "../${NAME}_patched.zip" . )
```

> 建議：打包前確認 zip 根目錄包含 `manifest.yaml`、`requirements.txt`、`main.py`/`main_impl.py` 等必要檔案（不能多包一層資料夾）。

---

## 4) 匯入前：刪除同名（避免 DUPLICATE）
> 平台的 import2 會用 suite+name 判定 DUPLICATE，所以建議先刪同名。

先查是否已有同名（避免誤刪）：
```bash
curl -sS "$CHARTER_BASE/api/scripts?suite=$SUITE&q=$NAME" | jq .
```

刪除該 script（破壞性操作，請確認）：
```bash
# 若你確定只會回 1 筆，可用 jq 抓 id；或直接手動填 script_id
OLD_ID=$SCRIPT_ID
curl -sS -X DELETE "$CHARTER_BASE/api/scripts/$OLD_ID" | jq .
```

---

## 5) Import2 修正版 zip
```bash
curl -sS -X POST "$CHARTER_BASE/api/scripts/import2" \
  -F "suite=$SUITE" \
  -F "file=@./${NAME}_patched.zip;type=application/zip" | jq .
```

回應 `created` 代表成功，會拿到新的 `id`。

---

## 6) Run 驗證
```bash
# 用名稱查回新的 script_id
NEW_ID=$(curl -sS "$CHARTER_BASE/api/scripts?suite=$SUITE&q=$NAME" | jq -r '.[0].id')

curl -sS -X POST "$CHARTER_BASE/api/scripts/$NEW_ID/run" | jq .
```

---

## 常見錯誤
### (1) import2 → `skipped:DUPLICATE`
- 原因：同 suite 下已存在同名 name
- 解法：先刪同名再匯入

### (2) import2 → `failed:MISSING_FILES`
- 原因：zip 內容缺 `manifest.yaml`/`requirements.txt`/`main.py`
- 解法：檢查你打包時是否多包了一層資料夾

### (3) run 時 entry resolve 失敗
- 原因：manifest 的 `entrypoint`/`entry` 指到不存在的檔案/函式
- 解法：`GET /api/scripts/{id}/manifest` 檢查 entrypoint
