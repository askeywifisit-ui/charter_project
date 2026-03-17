# 新增腳本（Create New Script）— Test Plan → Script ZIP → Import → Run → Evidence

當你沒有現成 script 可改（Modify），需要 **從 0 產生新的 test case 腳本** 時，照本頁做即可。

---

## 成功標準

1. 產出新 zip：`./${NAME}.zip`
2. `manifest.yaml` 命名與入口正確：`suite/name/entrypoint/env`
3. Import2 成功取得 `SCRIPT_ID`
4. Run 成功取得 `RID`
5. Evidence 已抓：`run_${RID}_log.json`（必要時含 log-archive）

---

## Sanity / Stability（suite 選擇與腳本架構）

### 何時放 sanity？何時放 stability？

- **sanity**：功能/流程驗證（一次性），通常 1~10 分鐘內跑完；重點是「可重跑、可取證、Fail 好定位」。
- **stability**：長跑/壓力/反覆循環（reboot/power-cycle/speedtest…）；重點是「循環控制、週期回報、容錯與恢復」。

### Manifest（env）架構建議

**Sanity（一次跑完）範例：**
```yaml
suite: sanity
entrypoint: main_impl.py:run

env:
  # 以單次流程為主；不要硬塞 cycles
  TIMEOUT_SEC: '60'
  RETRIES: '3'
  RETRY_INTERVAL_SEC: '3'
```

**Stability（循環/長跑）範例：**
```yaml
suite: stability
entrypoint: cycle_wrapper.py:run

env:
  # 必備：循環控制
  CYCLES: '48'
  CYCLE_INTERVAL: '600'
  STOP_ON_FAIL: '0'
  # 把真正測試入口交給 wrapper
  ORIGINAL_ENTRY: main_impl.py:run

  # 建議：每輪/每段輸出摘要（給人看）
  REPORT_EVERY_N_CYCLES: '1'
```

> 原則：**API 優先**；敏感值不進 zip（NOC/warehouse/SSH 密碼走 `.secrets/` 或 `dut.env`）。

---

## 0) 輸入資料（交給 OpenClaw 測試助理）

最少提供：
- `PRD_ID`（例：`C15807241`）
- `Test_case_name`（一句話）
- `Test Steps`（條列：precondition / action / expected）

命名規則：
- `NAME=<PRD_ID>_<Test_case_name>`（空白改 `_`）

> 安全原則：**敏感值不進 zip**。NOC/warehouse/SSH 密碼等一律放 `.secrets/`（或 systemd / `dut.env`）。

---

## 1) 先找可參考的既有腳本（推薦）

若平台上已有相似腳本：先 export zip，讓助理以「相似腳本 + 新 test steps」產生新腳本（更快、更穩）。

### 建議優先參考的基礎架構（C00000001 ~ C00000004）

這幾支是最常被拿來當「新腳本骨架」的基礎 case：

- `C00000001_SSH_basic_test`：SSH/連線與基本 precondition（適合需要 SSH 的 case）
- `C00000002_SSH_disable_test`：SSH disable/收尾流程（適合需要驗證關閉/復原）
- `C00000003_WIFI_basic_test`：Wi‑Fi 連線、拿 IP、ping router/internet 的 smoke 骨架
- `C00000004_NOC_API_basic_test`：NOC API flow / location context / 基本查詢的骨架

建議做法：
1) 先 export 其中一支最相近的 zip
2) 以該 zip 的 `manifest.yaml env` 與 logging 風格為模板，再把你的 test steps 塞進 `main_impl.py`

---

## 2) 產生腳本內容（建議由 OpenClaw 測試助理協助）

建議用 OpenClaw 測試助理來做「新腳本產生」工作：
- 能先找相似腳本當骨架（C00000001~04 或同模組腳本）
- 能依 test steps 自動補齊 manifest/env、timeouts、retry/backoff 與 log（evidence）格式
- 能依 DA40 習慣維持：**API 優先**、敏感值不進 zip、可重跑/可取證

你只要提供：`PRD_ID + Test_case_name + Test Steps`（以及是否允許 reboot/PDU/FR），助理就能產出可 import 的 zip。

新腳本 zip 建議包含：
- `manifest.yaml`
- `main_impl.py`（主要邏輯）
- `main.py`（薄 wrapper / 兼容入口）
- `requirements.txt`（需要才放）
- （可選）`cycle_wrapper.py`（需要 cycles/長跑時）

---

## 3) 打包 ZIP（根目錄不要多一層）

```bash
NAME="<NAME>"
( cd "$NAME" && zip -qr "../${NAME}.zip" . )
unzip -l "${NAME}.zip" | head
```

---

## 4) Import 到 Charter（Import2）

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

---

## 5) Run + Evidence

```bash
SCRIPT_ID=<FILL>

curl -sS -X POST "$CHARTER_BASE/api/scripts/$SCRIPT_ID/run" | python3 -m json.tool
RID=<RUN_ID>

curl -sS "$CHARTER_BASE/api/runs/$RID/log" > run_${RID}_log.json
ls -lh run_${RID}_log.json

#（可選）Fail 時抓 log archive
curl -sS "$CHARTER_BASE/api/runs/$RID/log-archives" | python3 -m json.tool
curl -fsSL "$CHARTER_BASE/api/runs/$RID/log-archive" -o run_${RID}_cpe_log.tar.gz
```

---

## 相關頁面

- [Modify Script Code](modify_script_code/)
- [Scripts 管理](scripts/)
- [腳本修改 SOP（入口）](script_change_sop/)
