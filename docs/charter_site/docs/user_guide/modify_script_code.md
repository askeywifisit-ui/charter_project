# Modify Script Code（改 zip 內 Python 程式碼）

> 入口（同事照做版）：[腳本修改 SOP（Export → Modify → Import → Run → Evidence）](script_change_sop.md)

本頁定位：補充「改 zip 內 code」的細節與常見踩雷點。

---

## TL;DR（最常見踩雷點）

1) **先備份**：Export zip（不備份很容易回不去）
2) **zip 根目錄不要多包一層資料夾**（最常見 `MISSING_FILES`）
3) **entrypoint 要對**（`manifest.yaml` 的 `entrypoint`/`entry` 要指到存在的檔案/函式）

---

## 0) 先設定 base

```bash
export CONTROL_PC_IP="<fill>"
export CHARTER_BASE="http://${CONTROL_PC_IP}:5173"
```

---

## 1) 找到 script（用 suite + name 查）

> 建議：用 `GET /api/scripts?limit=2000` 一次抓全量，再用 python 篩選（避免不同版本 API 搜尋行為差異）。

```bash
export SUITE="sanity"
export NAME="<SCRIPT_NAME>"

curl -fsSL "$CHARTER_BASE/api/scripts?limit=2000" \
  | python3 - <<'PY'
import json,os,sys
xs=json.load(sys.stdin)
name=os.environ.get('NAME')
suite=os.environ.get('SUITE')
ms=[s for s in xs if s.get('suite')==suite and s.get('name')==name]
print('matches:', len(ms))
for s in ms[:5]:
    print('id=', s.get('id'), 'suite=', s.get('suite'), 'name=', s.get('name'))
PY
```

---

## 2) Export zip（先備份）

```bash
export SCRIPT_ID=<SCRIPT_ID>
mkdir -p backup_scripts
curl -fsSL "$CHARTER_BASE/api/scripts/$SCRIPT_ID/export" \
  -o "backup_scripts/${NAME}_${SCRIPT_ID}.zip"
ls -lh "backup_scripts/${NAME}_${SCRIPT_ID}.zip"
```

---

## 3) 解壓 → 修改程式碼 → 重新打包

```bash
WORKDIR="work_${NAME}_${SCRIPT_ID}"
rm -rf "$WORKDIR" && mkdir -p "$WORKDIR"
unzip -q "backup_scripts/${NAME}_${SCRIPT_ID}.zip" -d "$WORKDIR"

# 修改（用你習慣的編輯器）
# vi "$WORKDIR/main_impl.py"

# 重新打包（注意：zip 根目錄不要多包一層資料夾）
( cd "$WORKDIR" && zip -qr "../${NAME}_patched.zip" . )

# 檢查 zip 根目錄（你應該看到 manifest.yaml / requirements.txt / main.py...）
unzip -l "./${NAME}_patched.zip" | head
```

---

## 4) 匯入前：刪除同名（避免 DUPLICATE）

> 這是破壞性動作；請確認你已經 export 備份。

```bash
OLD_ID=<OLD_ID>
curl -sS -X DELETE "$CHARTER_BASE/api/scripts/$OLD_ID" | python3 -m json.tool
```

---

## 5) Import2 修正版 zip

```bash
curl -sS -X POST "$CHARTER_BASE/api/scripts/import2" \
  -F "suite=$SUITE" \
  -F "file=@./${NAME}_patched.zip;type=application/zip" \
  | python3 -m json.tool
```

---

## 6) Run 驗證

```bash
# 找回新的 script_id
NEW_ID=$(curl -fsSL "$CHARTER_BASE/api/scripts?limit=2000" \
  | python3 - <<'PY'
import json,os,sys
xs=json.load(sys.stdin)
name=os.environ.get('NAME')
suite=os.environ.get('SUITE')
ms=[s for s in xs if s.get('suite')==suite and s.get('name')==name]
print(ms[0]['id'] if ms else '')
PY
)

echo "NEW_ID=$NEW_ID"

curl -sS -X POST "$CHARTER_BASE/api/scripts/$NEW_ID/run" | python3 -m json.tool
```

---

## 常見錯誤（對照表）

### (1) import2 → `skipped:DUPLICATE`
- 原因：同 suite 下已存在同名 name
- 解法：先刪同名再匯入

### (2) import2 → `failed:MISSING_FILES`
- 原因：zip 內容缺 `manifest.yaml`/`requirements.txt`/`main.py`
- 解法：檢查你打包時是否多包了一層資料夾（先跑 `unzip -l ... | head`）

### (3) run 時 entry resolve 失敗
- 原因：manifest 的 `entrypoint`/`entry` 指到不存在的檔案/函式
- 解法：用 `/api/scripts/{id}/manifest` 檢查 entrypoint
