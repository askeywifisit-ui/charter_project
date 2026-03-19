# 交付下載（Scripts / Web / API / Tools）

本頁提供「從 GitHub 下載交付包」的固定連結，方便外部單位/新環境快速取得檔案。

> Repo：<https://github.com/askeywifisit-ui/charter_project>

## 1) Scripts（測試腳本）

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
| `charter_api_20260310_201313.tar.gz` | ~30MB | Charter API 程式 |
| `charter_web_20260310_201313.tar.gz` | ~23MB | Charter Web UI 程式 |
| `charter_tools_20260310_201313.tar.gz` | ~264KB | Charter Tools 工具 |
| `charter_systemd_units_11F_140_20260311_105846.tar.gz` | ~1KB | Systemd 服務設定檔 |

## 3) 校驗（下載後建議執行）

```bash
# 檢查 SHA256
shasum -a 256 charter_api_20260310_201313.tar.gz
shasum -a 256 charter_web_20260310_201313.tar.gz
shasum -a 256 charter_tools_20260310_201313.tar.gz
```

## 4) 解壓縮

```bash
tar -xzf charter_api_20260310_201313.tar.gz -C /home/da40/
tar -xzf charter_web_20260310_201313.tar.gz -C /home/da40/
tar -xzf charter_tools_20260310_201313.tar.gz -C /home/da40/
tar -xzf charter_systemd_units_11F_140_20260311_105846.tar.gz -C /etc/systemd/system/
```

## 5) 資料庫 Schema（新架站用）

> 新架站只需要 schema，不需要實際測試資料

- Schema 檔案：<https://github.com/askeywifisit-ui/charter_project/tree/main/database>
- 直接下載：<https://github.com/askeywifisit-ui/charter_project/raw/main/database/rg_schema_only.sql>

### 還原資料庫 Schema

```bash
# 在新機器執行
curl -O https://github.com/askeywifisit-ui/charter_project/raw/main/database/rg_schema_only.sql
sudo -iu postgres psql -d rg -f rg_schema_only.sql
```

## 6) 完整資料庫備份（可選）

> ⚠️ 大檔案（53MB），建議只在需要完整資料時下載

- 完整備份（壓縮）：<https://github.com/askeywifisit-ui/charter_project/tree/main/database>
- 下載：`rg_full_backup.sql.gz`（約 53MB）

### 還原完整資料庫

```bash
# 下載並解壓
curl -O https://github.com/askeywifisit-ui/charter_project/raw/main/database/rg_full_backup.sql.gz
gunzip rg_full_backup.sql.gz

# 還原
sudo -iu postgres psql -d rg -f rg_full_backup.sql
```
