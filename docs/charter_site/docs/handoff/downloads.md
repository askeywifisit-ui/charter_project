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

## 2) Web / API / Tools（平台程式與工具包）

> **直接下載**：請到以下頁面點擊各檔案進行下載
> <https://github.com/askeywifisit-ui/charter_project/tree/main/packages>

| 檔案 | 大小 | 說明 |
|------|------|------|
| `charter_api.tar.gz` | ~30MB | Charter API 程式 |
| `charter_web.tar.gz` | ~23MB | Charter Web UI 程式 |
| `charter_tools.tar.gz` | ~264KB | Charter Tools 工具 |
| `charter_systemd_units.tar.gz` | ~618B | Systemd 服務設定檔 |

## 3) 校驗（下載後建議執行）

```bash
# 檢查 SHA256
shasum -a 256 charter_api.tar.gz
shasum -a 256 charter_web.tar.gz
shasum -a 256 charter_tools.tar.gz
shasum -a 256 charter_systemd_units.tar.gz
```

## 4) 解壓縮

```bash
tar -xzf charter_api.tar.gz -C /home/da40/
tar -xzf charter_web.tar.gz -C /home/da40/
tar -xzf charter_tools.tar.gz -C /home/da40/
tar -xzf charter_systemd_units.tar.gz -C /etc/systemd/system/
```
