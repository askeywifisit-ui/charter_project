# 腳本修改 SOP（Export → Modify → Import → Run → Evidence）

> 給 OpenClaw 測試助理：你可以直接讀懂這頁，並依這個 SOP **用 Charter API 協助我控制測試平台**（查 scripts / export / delete / import / run / 抓 log / purge）。

這頁是給內部同事的「一條龍流程」。

> 你只要照這頁做，就能：**備份 → 修改 zip → 避免 DUPLICATE → 匯入 → 跑 run → 抓 log/證據**。

---

## 0) 先填基本變數

```bash
export CONTROL_PC_IP="<fill>"     # 例：172.14.1.140
export CHARTER_BASE="http://${CONTROL_PC_IP}:5173"
export SUITE="sanity"            # sanity 或 stability
export NAME="<SCRIPT_NAME>"       # 例：C00000001_SSH_basic_test
```

---

## 1) 找 script_id（用名稱查）

```bash
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

把 id 記下來（下例用 `SCRIPT_ID`）。

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
ls -lh "./${NAME}_patched.zip"
```

---

## 4) 匯入前：刪除同名（避免 DUPLICATE）

> 規則：**同 suite + 同 name** 必須先刪再匯入。

```bash
# 先查同名（確認只有你要刪的那筆）
curl -fsSL "$CHARTER_BASE/api/scripts?limit=2000" \
  | python3 - <<'PY'
import json,os,sys
xs=json.load(sys.stdin)
name=os.environ.get('NAME')
suite=os.environ.get('SUITE')
ms=[s for s in xs if s.get('suite')==suite and s.get('name')==name]
for s in ms:
    print('id=', s.get('id'), 'suite=', s.get('suite'), 'name=', s.get('name'))
PY

# 刪除（破壞性）
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

## 6) Run 驗證 + 抓 Evidence

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

# 送出 run
RID=$(curl -sS -X POST "$CHARTER_BASE/api/scripts/$NEW_ID/run" \
  | python3 - <<'PY'
import json,sys
print(json.load(sys.stdin).get('run_id',''))
PY
)

echo "RID=$RID"

# 抓 log
curl -sS "$CHARTER_BASE/api/runs/$RID/log" > run_${RID}_log.json
ls -lh run_${RID}_log.json
```

---

## 下一步（相關頁面）

- Scripts 管理（概念 + UI 截圖）：[Scripts 管理](scripts.md)
- Modify Script Code（詳細版）：[Modify Script Code](modify_script_code.md)
- Runs 操作（API 速查）：[Runs 操作](runs.md)
