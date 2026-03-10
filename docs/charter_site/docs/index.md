# Charter 平台文件站（預覽）

本文件站整理 Charter 自動化測試平台的 **操作手冊 / API 參考 / 維運與交付**。

## 人類版 Quick Start（先看這裡）

- **平台入口 / 常用頁面**
  - [Platform Links（平台入口）](platform_links/)
  - [Runs 操作（跑腳本 / 看 log / purge）](user_guide/runs/)
  - Test Suites： [Sanity](test_suites/sanity/) / [Stability](test_suites/stability/)
  - [Physical Topology（線怎麼接）](architecture/topology/)

- **最常見 3 個問題**
  - Wi‑Fi / route / iface： [Troubleshooting](runbook/troubleshooting/)
  - OAuth/Token / provider： [Troubleshooting](runbook/troubleshooting/)
  - Import DUPLICATE： [Scripts 管理](user_guide/scripts/)

> 需要「Agent 可執行版」： [Agent Runbook（給 AI）](runbook/agent_runbook/)

---

## 依角色入口（你是誰就點哪一區）

- **操作 / 驗證人員**： [Platform Links](platform_links/) → [Runs 操作](user_guide/runs/) → [Sanity](test_suites/sanity/) / [Stability](test_suites/stability/)
- **整合 / 自動化（API）**： [Workflows](api_reference/workflows/) / [Scripts](api_reference/scripts/) / [Runs](api_reference/runs/)
- **交付 / 換環境（移植）**： [Environment Template](environment_template/) / [Hand-off](handoff/)

---

## 維護者入口（文件怎麼改 / 怎麼上站）

- 專案位置與協作方式： [協作 / Repo / 路徑](operations/collaboration/)

```bash
cd ~/.openclaw/workspace/docs/charter_site
python3 -m mkdocs build
python3 -m mkdocs serve -a 127.0.0.1:8000
```

> 原則：只改 `docs/` 內的 Markdown；不要直接改 `site/`。

