# 交付下載（Scripts / Web / API / Tools）

本頁提供「從 GitHub 下載交付包」的固定連結，方便外部單位/新環境快速取得檔案。

> Repo：<https://github.com/askeywifisit-ui/charter_project>

## 1) Scripts（測試腳本 zip）

- Sanity（資料夾）：
  - <https://github.com/askeywifisit-ui/charter_project/tree/main/scripts/sanity>
- Stability（資料夾）：
  - <https://github.com/askeywifisit-ui/charter_project/tree/main/scripts/stability>
- 匯出清單（manifest）：
  - Sanity：<https://github.com/askeywifisit-ui/charter_project/raw/main/scripts/manifest_sanity.json>
  - Stability：<https://github.com/askeywifisit-ui/charter_project/raw/main/scripts/manifest_stability.json>

> 建議下載方式：直接 `git clone` 本 repo，或用 GitHub 介面下載資料夾/單一 zip。

## 2) Web / API / Tools（平台程式與工具包）

> ⚠️ **上傳狀態**：以下檔案需先上傳到 GitHub Releases 或 packages 目錄

- API（tar.gz）：
  - 本機檔案：`/home/da40/charter_api.tar.gz` (30MB)
  - 上傳後連結：<https://github.com/askeywifisit-ui/charter_project/releases>
- Web（tar.gz）：
  - 本機檔案：`/home/da40/charter_web.tar.gz` (23MB)
  - 上傳後連結：<https://github.com/askeywifisit-ui/charter_project/releases>
- Tools（tar.gz）：
  - 本機檔案：`/home/da40/charter_tools.tar.gz` (264KB)
  - 上傳後連結：<https://github.com/askeywifisit-ui/charter_project/releases>
- Systemd units（tar.gz）：
  - 本機檔案：`/home/da40/charter_systemd_units.tar.gz` (618B)
  - 上傳後連結：<https://github.com/askeywifisit-ui/charter_project/releases>

## 3) 手動上傳到 GitHub Releases

若需要上傳，請在 GitHub 頁面操作：
1. 開啟 <https://github.com/askeywifisit-ui/charter_project/releases>
2. 點「Create a new release」
3. 標題：`v1.0-migration-20260319`
4. 將以下檔案拖放進去：
   - `/home/da40/charter_api.tar.gz`
   - `/home/da40/charter_web.tar.gz`
   - `/home/da40/charter_tools.tar.gz`
   - `/home/da40/charter_systemd_units.tar.gz`

## 4) 校驗（建議必做）

```bash
# 下載後驗證
shasum -a 256 charter_api.tar.gz
shasum -a 256 charter_web.tar.gz
shasum -a 256 charter_tools.tar.gz
shasum -a 256 charter_systemd_units.tar.gz
```
