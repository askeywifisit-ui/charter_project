# Charter 測試平台 — 從零到上線

> 從零佈置 → 腳本管理 → 腳本開發 → 執行取證 → Debug → 系統維運

---

## 🚀 快速入口

| 任務 | 連結 |
|------|------|
| 平台入口（UI / API） | [Platform Links](platform_links/) |
| 測試腳本列表 | [Sanity](test_suites/sanity/) / [Stability](test_suites/stability/) |
| API 文件 | [Scripts API](api_reference/scripts/) / [Runs API](api_reference/runs/) |
| 系統拓撲 | [Physical Topology](architecture/topology/) |
| OpenClaw 設定 | [OpenClaw Setup](openclaw_setup/openclaw_test_assistant_setup/) |

---

## 📋 完整流程（依序）

### 1️⃣ 平台佈置（從零開始）

> 第一次搭建 Charter 測試平台？

- [平台安裝 / 移植](getting_started/platform_install/)
- [環境參數範本](environment_template/)
- [交接文件](handoff/index/)

---

### 2️⃣ 腳本管理（Import / Export / 刪除）

> 管理腳本：匯入、匯出、刪除

- [腳本匯入/匯出](user_guide/scripts/)
- [API 參考](api_reference/scripts/)

---

### 3️⃣ 腳本開發（Modify / Create）

> 修改現有腳本 or 建立新腳本

- [修改腳本代碼](user_guide/modify_script_code/)
- [新建腳本](user_guide/create_new_script/)
- [從 Test Plan 建立腳本](user_guide/create_new_script/)
- [一條龍 SOP](user_guide/script_change_sop/)

---

### 4️⃣ 執行與取證（Run & Evidence）

> 執行腳本、收集證據、清理

- [執行腳本](user_guide/runs/)
- [取證（Log / Screenshot）](user_guide/runs/)
- [清理 Runs](user_guide/runs/)

---

### 5️⃣ Debug & Trace

> 常見問題排查

- [常見問題排查](runbook/troubleshooting/)
- [Wi-Fi / Route / Iface 問題](runbook/troubleshooting/)
- [OpenClaw OAuth/Token 問題](runbook/troubleshooting/)

---

### 6️⃣ 系統維運

> 日常維運：重啟、監控、控制

- [重啟服務](platform_links/)
- [監控 / Health Check](platform_links/)
- [PDU 控制](tools/pdu/)
- [Tools 工具模組](tools/index/)

---

## 📚 參考文件

- [API Reference](api_reference/index/)
- [Architecture](architecture/topology/)
- [OpenClaw Setup](openclaw_setup/openclaw_test_assistant_setup/)

---

## 🤖 給 OpenClaw 測試助理

- [Agent Runbook](runbook/agent_runbook/)
- [OpenClaw Setup](openclaw_setup/openclaw_test_assistant_setup/)
