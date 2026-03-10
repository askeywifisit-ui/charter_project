# API Reference

本章整理 Charter 平台（FastAPI）的所有 HTTP API。

## Base URL
- UI: `http://{{CONTROL_PC_IP}}:5173`
- API: `http://{{CONTROL_PC_IP}}:5173/api`

以下 curl 範例會用：
```bash
export CHARTER_BASE="http://{{CONTROL_PC_IP}}:5173"
```

> 多數前端呼叫都是同源相對路徑（`/api/...`）。

## 來源與更新方式
- 來源：由 `system/api.zip`（FastAPI）靜態掃描與逐檔閱讀整理
- 目前採「文件化整理」；後續若平台提供 OpenAPI (`/openapi.json`) 可改為自動生成 + 人工補充。
