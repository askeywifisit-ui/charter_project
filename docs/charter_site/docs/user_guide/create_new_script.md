# 新增腳本（Create New Script）— 從 Test Plan 產生 zip → Import → Run → Evidence

本頁目的：當你沒有現成的 script 可以改（Modify），而是要 **從 0 產生一支新的 test case 腳本** 時，同事照著做就能完成：

- 產生新的 script zip（含 `manifest.yaml` + `main.py/main_impl.py`）
- 命名規則：`PRD_ID + Test_case_name`
- 由 OpenClaw 測試助理協助把 Test Plan（steps）轉成可跑腳本
- Import 到 Charter 測試平台並 Run，最後抓 evidence

---

## 成功標準（完成以下 5 項即可）

1. 你手上有新 zip：`./<NAME>.zip`
2. `manifest.yaml` 的 `suite/name/entrypoint/env` 完整
3. 平台 Import2 成功，取得 `SCRIPT_ID`
4. Run 成功產生 `RID`
5. Evidence 已抓：`run_${RID}_log.json`（必要時含 log-archive）

---

## 0) 你要先準備的輸入（提供給 OpenClaw 測試助理）

請提供以下資訊（最少要有 A+B）：

A) **命名**
- `PRD_ID`：例如 `C15807241` / `A2844344`
- `Test_case_name`：一句話描述
- 組合規則：`<PRD_ID>_<Test_case_name>`（空白改 `_`）

B) **Test Plan（Test Steps）**
- 建議格式：條列 step（每步的 precondition / action / expected）

C) **測試環境假設（重要）**
- 平台：11F_140 / 11F_131？control PC IP？
- 可能會 reboot / PDU reset / factory reset 嗎？
- 需要 NOC/warehouse/SSH/Wi‑Fi 哪些能力？

> 安全原則：請不要把密碼寫進 script zip；敏感值走 `.secrets/` + systemd / `dut.env`。

---

## 1) OpenClaw 協助產生腳本（建議工作流）

你可以直接對 OpenClaw 測試助理說：

- 「請依這份 test plan 產生一支新的 Charter script zip，name=`<NAME>`，suite=`sanity`，包含 manifest + main_impl.py，並遵守：API 優先、可重跑、log 一行 JSON。」

助理產出的內容通常包含：
- `manifest.yaml`
- `requirements.txt`（需要才放）
- `main_impl.py`（主要邏輯）
- `main.py`（薄 wrapper / 兼容入口）
-（可選）`cycle_wrapper.py`（需要 cycles/重跑時）

---

## 2) 打包成 zip（根目錄不要多一層）

目錄結構（範例）：
```text
<NAME>/
  manifest.yaml
  requirements.txt
  main.py
  main_impl.py
```

打包：
```bash
NAME="<NAME>"
( cd "$NAME" && zip -qr "../${NAME}.zip" . )

unzip -l "${NAME}.zip" | head
```

---

## 3) Import 到 Charter 平台（Import2）

```bash
export CONTROL_PC_IP="172.14.1.140"
export CHARTER_BASE="http://${CONTROL_PC_IP}:5173"
export SUITE="sanity"
NAME="<NAME>"

curl -sS -X POST "$CHARTER_BASE/api/scripts/import2" \
  -F "suite=$SUITE" \
  -F "file=@./${NAME}.zip;type=application/zip" \
  | python3 -m json.tool
```

把回應裡的 `id` 記下來（即 `SCRIPT_ID`）。

---

## 4) Run 驗證 + Evidence

```bash
SCRIPT_ID=<FILL>

# Run
curl -sS -X POST "$CHARTER_BASE/api/scripts/$SCRIPT_ID/run" | python3 -m json.tool

# 把 run_id 記下來
RID=<RUN_ID>

# Evidence
curl -sS "$CHARTER_BASE/api/runs/$RID/log" > run_${RID}_log.json
ls -lh run_${RID}_log.json

#（可選）Fail 時抓 log archive
curl -sS "$CHARTER_BASE/api/runs/$RID/log-archives" | python3 -m json.tool
curl -fsSL "$CHARTER_BASE/api/runs/$RID/log-archive" -o run_${RID}_cpe_log.tar.gz
```

---

## 5) 建議規範（避免未來維護成本）

- **API 優先**：能用 `/api/...` 就不要用 UI 操作。
- **敏感值不進 zip**：NOC/warehouse/SSH password 都放 `.secrets/` 或 `dut.env`。
- **Log 可讀**：建議一行 JSON（jlog），方便從 run log 快速摘要 PASS/FAIL。
- **可重跑**：加 retry/backoff、明確 timeout；避免只靠 sleep。

---

## 相關頁面

- Modify Script Code（改現成腳本）：[Modify Script Code](modify_script_code.md)
- Scripts 管理（Import/Export/Delete）：[Scripts 管理](scripts.md)
- 腳本修改 SOP（入口，一條龍）：[腳本修改 SOP（入口）](script_change_sop.md)
