# Charter 測試平台（從零到上線）

> 從零佈置 → 腳本管理 → 腳本開發 → 執行取證 → Debug → 系統維運

---

## 1️⃣ 平台佈置（從零開始）

- [平台安裝 / 移植](getting_started/platform_install.md)
- [環境參數範本](environment_template.md)
- [交接文件](handoff/index.md)

---

## 2️⃣ 腳本管理（Import/Export/刪除）

- [腳本匯入/匯出](user_guide/scripts.md)
- [Import 前刪除同名腳本](user_guide/scripts.md#import-前刪除同名腳本)
- [API 參考](api_reference/scripts.md)

---

## 3️⃣ 腳本開發（Modify/Create）

- [修改腳本代碼](user_guide/modify_script_code.md)
- [新建腳本](user_guide/create_new_script.md)
- [從 Test Plan 建立腳本](user_guide/create_new_script.md#從-test-plan-建立腳本)
- [一條龍 SOP](user_guide/script_change_sop.md)

---

## 4️⃣ 執行與取證（Run & Evidence）

- [執行腳本](user_guide/runs.md)
- [取證（Log / Screenshot）](user_guide/runs.md#取證)
- [清理 Runs](user_guide/runs.md#purge-清理)

---

## 5️⃣ Debug & Trace

- [常見問題排查](runbook/troubleshooting.md)
- [Wi-Fi / Route / Iface 問題](runbook/troubleshooting.md#4-wi-fi--route--iface-相關問題測試機網路面)
- [OpenClaw OAuth/Token 問題](runbook/troubleshooting.md#5-oauth--token--provideropenclaw)

---

## 6️⃣ 系統維運

- [重啟服務](platform_links.md)
- [監控 / Health Check](platform_links.md)
- [PDU 控制](tools/pdu.md)

---

## 常用入口

- [Platform Links（平台入口）](platform_links.md)
- [Test Suites](test_suites/sanity.md)
- [Physical Topology](architecture/topology.md)
- [Tools 工具模組](tools/index.md)

---

## 給 OpenClaw 測試助理

- [OpenClaw Setup](openclaw_setup/openclaw_test_assistant_setup.md)
- [Agent Runbook](runbook/agent_runbook.md)
