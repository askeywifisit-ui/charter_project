# 腳本修改 SOP（Export → Modify → Import → Run → Evidence）

!!! tip "給 OpenClaw 測試助理"

    你可以依本頁流程，用 Charter API 協助我控管測試平台（查 scripts / export / delete / import / run / 抓 log/證據 / purge）。

本頁定位：**一條龍 SOP**。目的不是講 API 文件，而是讓同事第一次照做就能成功「改一個腳本、跑起來、拿到證據」。

---

## 成功標準（完成以下 3 項即可）

1. 已完成備份：`backup_scripts/${NAME}_${SCRIPT_ID}.zip`
2. 已完成重新匯入並可執行：已取得 `NEW_ID`，且 Run 成功產生 `RID`
3. 已完成取證：已下載 `run_${RID}_log.json`

---

## 你只要先搞懂的 4 個重點（第一次照做不會卡）

### 1) CHARTER_BASE 是哪裡？
- 就是 control PC 的 UI base，例如：`http://172.14.1.140:5173`
- 不確定 control PC IP：看文件站 **Platform Links** 或問維護者。

### 2) SCRIPT_ID / OLD_ID / NEW_ID 的差別（最常搞混）
- `SCRIPT_ID`：你要 **export 備份** 的那筆
- `OLD_ID`：你要 **刪掉** 的那筆（通常就是舊的同名 script，用來避免 `DUPLICATE`）
- `NEW_ID`：你 **import2 後新產生** 的那筆（要 run 請用它）

### 3) 刪同名避免 DUPLICATE 是破壞性動作
- 刪除會影響其他人（同名 script 會消失）
- 標準流程：**先 export 備份再刪**

### 4) zip 打包最常踩雷：根目錄不要多一層資料夾
重新打包後先檢查：

```bash
unzip -l ${NAME}_patched.zip | head
# 你應該看到 manifest.yaml / requirements.txt / main.py... 在 zip 根目錄
```

---

## 0) 先填基本變數（務必先做）

> 建議：先用最小 smoke case（sanity 的 basic 類）練一次流程。

```bash
export CONTROL_PC_IP="<fill>"       # 例：172.14.1.140
export CHARTER_BASE="http://${CONTROL_PC_IP}:5173"
export SUITE="sanity"              # sanity 或 stability
export NAME="<SCRIPT_NAME>"         # 例：C00000001_SSH_basic_test

# （快速自檢）確認變數有值，且 API 可達
echo "CHARTER_BASE=[$CHARTER_BASE] SUITE=[$SUITE] NAME=[$NAME]"
curl -fsSL "$CHARTER_BASE/api/health"; echo
```

> 若你看到 `curl: (3) URL using bad/illegal format`：幾乎都是 `CHARTER_BASE` 沒 export 或字串少了 `http://`。

---

## 1) 找 script_id（用名稱查）

> ⚠️ 不建議用「curl | python heredoc」直接 pipe 解析：貼到 terminal 時常因縮排/編碼導致 python 提早退出，進而觸發 `curl: (23) Failure writing output`。
>
> 以下提供一個 **穩定版**（先存檔再解析），同事照貼成功率最高。

```bash
curl -fsSL "$CHARTER_BASE/api/scripts?limit=2000" -o /tmp/scripts.json

python3 - <<'PY'
import json,os
xs=json.load(open('/tmp/scripts.json'))
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

# 快速檢查 zip 根目錄
unzip -l "./${NAME}_patched.zip" | head
```

---

## 4) 匯入前：刪除同名（避免 DUPLICATE）

> 規則：**同 suite + 同 name** 必須先刪再匯入。
>
> ⚠️ 這段開始會動到平台資料（破壞性）。第一次照做前，建議先做下面的 Dry-run 檢查清單。

### 4.0 Dry-run（安全檢查清單 / 不會改動平台）

```bash
# 0) 變數自檢（必做）
echo "CHARTER_BASE=[$CHARTER_BASE] SUITE=[$SUITE] NAME=[$NAME]"
curl -fsSL "$CHARTER_BASE/api/health"; echo

# 1) 確認手上 patched zip 存在
ls -lh "./${NAME}_patched.zip"

# 2) 重新確認平台上「同名 script」有哪些（你等等要刪的是哪一筆）
curl -fsSL "$CHARTER_BASE/api/scripts?limit=2000" -o /tmp/scripts.json
python3 - <<'PY'
import json,os
xs=json.load(open('/tmp/scripts.json'))
name=os.environ.get('NAME')
suite=os.environ.get('SUITE')
ms=[s for s in xs if s.get('suite')==suite and s.get('name')==name]
print('matches:',len(ms))
for s in ms:
    print('id=', s.get('id'), 'suite=', s.get('suite'), 'name=', s.get('name'))
PY

# 3) 確認 worker 正常（否則 run 會 queued）
curl -fsSL "$CHARTER_BASE/api/runs/worker/status" | python3 -m json.tool
```

```bash
# 先查同名（確認只有你要刪的那筆）
curl -fsSL "$CHARTER_BASE/api/scripts?limit=2000" -o /tmp/scripts.json

python3 - <<'PY'
import json,os
xs=json.load(open('/tmp/scripts.json'))
name=os.environ.get('NAME')
suite=os.environ.get('SUITE')
ms=[s for s in xs if s.get('suite')==suite and s.get('name')==name]
for s in ms:
    print('id=', s.get('id'), 'suite=', s.get('suite'), 'name=', s.get('name'))
PY

# 刪除（破壞性）
# 建議：先 export 備份完成，再刪。
OLD_ID=<OLD_ID>

# （最後確認）你要刪的是哪一筆
curl -fsSL "$CHARTER_BASE/api/scripts?limit=2000" -o /tmp/scripts.json
python3 - <<'PY'
import json,os
xs=json.load(open('/tmp/scripts.json'))
name=os.environ.get('NAME')
suite=os.environ.get('SUITE')
ms=[s for s in xs if s.get('suite')==suite and s.get('name')==name]
print('matches:',len(ms))
for s in ms:
    print('id=', s.get('id'), 'suite=', s.get('suite'), 'name=', s.get('name'))
PY

echo "Deleting OLD_ID=$OLD_ID"  # 讓同事看清楚再按 Enter
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
curl -fsSL "$CHARTER_BASE/api/scripts?limit=2000" -o /tmp/scripts.json

NEW_ID=$(python3 - <<'PY'
import json,os
xs=json.load(open('/tmp/scripts.json'))
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

# 抓 log（evidence）
curl -sS "$CHARTER_BASE/api/runs/$RID/log" > run_${RID}_log.json
ls -lh run_${RID}_log.json
```

---

## 下一步（相關頁面）

- Scripts 管理（概念 + UI 截圖）：[Scripts 管理](scripts.md)
- Modify Script Code（詳細版）：[Modify Script Code](modify_script_code.md)
- Runs 操作（API 速查）：[Runs 操作](runs.md)
