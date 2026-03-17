# 協作 / Repo / 路徑（給維護者）

這頁給「要一起改文件、或要把文件站搬到別台機器」的人。

## Repo / 目錄位置（Alice 主機）

- Repo（OpenClaw workspace）：`/Users/csit/.openclaw/workspace`
- 文件站來源（MkDocs 專案根）：`/Users/csit/.openclaw/workspace/docs/charter_site/`
  - `mkdocs.yml`：MkDocs 設定
  - `docs/`：Markdown 原始檔（唯一來源）
  - `site/`：build 輸出（靜態網站）

## Sanity 頁面來源對照

- Sanity index：`docs/charter_site/docs/test_suites/sanity.md`
- 單一 case：`docs/charter_site/docs/test_suites/sanity/<CASE_NAME>.md`

## 本機預覽 / Build

```bash
cd /Users/csit/.openclaw/workspace/docs/charter_site
python3 -m pip install -U mkdocs mkdocs-material
mkdocs serve -a 127.0.0.1:8000
```

打開：<http://127.0.0.1:8000/>

> 原則：改 `docs/` 內的 `.md` 後再 rebuild/serve；不要直接改 `site/`。
