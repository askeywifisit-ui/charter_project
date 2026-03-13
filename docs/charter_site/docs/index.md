# Charter 測試平台文件（Overview）

這裡整理的是 **Charter 自動化測試平台** 的操作方法與技術資料（SOP / API 參考 / 維運與交付）。

> 文件站本身只是「呈現方式」；內容主體是 Charter 測試平台的知識與流程。

## 人類版 Quick Start（先看這裡）

- **平台入口 / 常用頁面**
  - [Platform Links（平台入口）](platform_links.md)
  - [Runs 操作（跑腳本 / 看 log / purge）](user_guide/runs.md)
  - Test Suites： [Sanity](test_suites/sanity.md) / [Stability](test_suites/stability.md)
  - [Physical Topology（線怎麼接）](architecture/topology.md)

- **最常見 3 個問題**
  - Wi‑Fi / route / iface： [Troubleshooting](runbook/troubleshooting.md)
  - OAuth/Token / provider： [Troubleshooting](runbook/troubleshooting.md)
  - Import DUPLICATE： [Scripts 管理](user_guide/scripts.md)

> 需要「Agent 可執行版」： [Agent Runbook（給 AI）](runbook/agent_runbook.md)
>
> Demo（工程向 15–20 分鐘）：[Runbook → Demo 場景（工程向）](runbook/demo_scenario_openclaw.md)

---

## 依角色入口（你是誰就點哪一區）

- **操作 / 驗證人員**： [Platform Links](platform_links.md) → [Runs 操作](user_guide/runs.md) → [Sanity](test_suites/sanity.md) / [Stability](test_suites/stability.md)
- **整合 / 自動化（API）**： [Workflows](api_reference/workflows.md) / [Scripts](api_reference/scripts.md) / [Runs](api_reference/runs.md)
- **交付 / 換環境（移植）**： [Environment Template](environment_template.md) / [Hand-off](handoff/index.md)

---

## 維護者入口（文件怎麼改 / 怎麼上站）

- 專案位置與協作方式： [協作 / Repo / 路徑](operations/collaboration.md)

```bash
cd ~/.openclaw/workspace/docs/charter_site
python3 -m mkdocs build
python3 -m mkdocs serve -a 127.0.0.1:8000
```

> 原則：只改 `docs/` 內的 Markdown；不要直接改 `site/`。

