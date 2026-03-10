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

- API（tar.gz）：
  - <https://github.com/askeywifisit-ui/charter_project/raw/main/packages/charter_api_20260310_201313.tar.gz>
- Web（tar.gz）：
  - <https://github.com/askeywifisit-ui/charter_project/raw/main/packages/charter_web_20260310_201313.tar.gz>
- Tools（tar.gz）：
  - （暫不提供公開連結；請由內部管道取得）
- SHA256SUMS：
  - <https://github.com/askeywifisit-ui/charter_project/raw/main/packages/SHA256SUMS.txt>

## 3) 校驗（建議必做）

```bash
curl -fL -o SHA256SUMS.txt \
  https://github.com/askeywifisit-ui/charter_project/raw/main/packages/SHA256SUMS.txt

shasum -a 256 -c SHA256SUMS.txt
```
