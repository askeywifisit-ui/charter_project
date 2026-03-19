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

## 5) 資料庫 Schema（新架站用）

> 新架站只需要 schema，不需要實際測試資料

- Schema 檔案：<https://github.com/askeywifisit-ui/charter_project/tree/main/database>
- 直接下載：<https://github.com/askeywifisit-ui/charter_project/raw/main/database/rg_schema_only.sql>

### 還原資料庫 Schema

```bash
# 在新機器執行
sudo -iu postgres psql -d rg -f rg_schema_only.sql
```

### 參考：完整資料庫匯出（包含測試資料）

如需完整備份（含資料），可自行在 172.14.1.140 執行：

```bash
# 完整匯出
PGPASSWORD=rg pg_dump -U rg -h 127.0.0.1 rg > rg_full_backup.sql

# 只匯出資料（不含 schema）
PGPASSWORD=rg pg_dump -U rg -h 127.0.0.1 rg --data-only > rg_data_only.sql
```
