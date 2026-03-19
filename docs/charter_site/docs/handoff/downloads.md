# 下載交付包

> 本頁提供從 GitHub 下載 Charter 交付包的連結。

---

## 📦 交付包下載

### Packages（程式與工具）

| 檔案 | 大小 | 說明 |
|:-----|:----:|:-----|
| [📦 charter_api.tar.gz](https://github.com/askeywifisit-ui/charter_project/raw/main/packages/charter_api_20260310_201313.tar.gz) | ~30MB | API 程式 |
| [📦 charter_web.tar.gz](https://github.com/askeywifisit-ui/charter_project/raw/main/packages/charter_web_20260310_201313.tar.gz) | ~23MB | Web UI 程式 |
| [📦 charter_tools.tar.gz](https://github.com/askeywifisit-ui/charter_project/raw/main/packages/charter_tools_20260310_201313.tar.gz) | ~264KB | 工具腳本 |
| [📦 charter_systemd.tar.gz](https://github.com/askeywifisit-ui/charter_project/raw/main/packages/charter_systemd_units_11F_140_20260311_105846.tar.gz) | ~1KB | Systemd 設定 |

> 📌 或從 [GitHub Packages 頁面](https://github.com/askeywifisit-ui/charter_project/tree/main/packages) 下載

---

### 📂 Scripts（測試腳本）

| 類型 | 連結 |
|:-----|:-----|
| Sanity（資料夾） | [📁 scripts/sanity](https://github.com/askeywifisit-ui/charter_project/tree/main/scripts/sanity) |
| Stability（資料夾） | [📁 scripts/stability](https://github.com/askeywifisit-ui/charter_project/tree/main/scripts/stability) |
| Sanity Manifest | [📄 manifest_sanity.json](https://github.com/askeywifisit-ui/charter_project/raw/main/scripts/manifest_sanity.json) |
| Stability Manifest | [📄 manifest_stability.json](https://github.com/askeywifisit-ui/charter_project/raw/main/scripts/manifest_stability.json) |

---

### 🗄️ 資料庫

| 檔案 | 大小 | 說明 |
|:-----|:----:|:-----|
| [🗄️ rg_schema_only.sql](https://github.com/askeywifisit-ui/charter_project/raw/main/database/rg_schema_only.sql) | ~14KB | Schema 結構（推薦） |
| [🗄️ rg_full_backup.sql.gz](https://github.com/askeywifisit-ui/charter_project/raw/main/database/rg_full_backup.sql.gz) | ~53MB | 完整備份（含資料） |

---

## 📥 下載與解壓指令

```bash
# 下載 Packages
curl -O https://github.com/askeywifisit-ui/charter_project/raw/main/packages/charter_api_20260310_201313.tar.gz
curl -O https://github.com/askeywifisit-ui/charter_project/raw/main/packages/charter_web_20260310_201313.tar.gz
curl -O https://github.com/askeywifisit-ui/charter_project/raw/main/packages/charter_tools_20260310_201313.tar.gz

# 下載 Schema
curl -O https://github.com/askeywifisit-ui/charter_project/raw/main/database/rg_schema_only.sql
```

---

## 📂 解壓縮

```bash
# 解壓到正確位置
tar -xzf charter_api_20260310_201313.tar.gz -C /home/da40/
tar -xzf charter_web_20260310_201313.tar.gz -C /home/da40/
tar -xzf charter_tools_20260310_201313.tar.gz -C /home/da40/
sudo tar -xzf charter_systemd_units_11F_140_20260311_105846.tar.gz -C /etc/systemd/system/
```

---

## 🗄️ 資料庫匯入

```bash
# Schema（推薦）
sudo -iu postgres psql -d rg -f rg_schema_only.sql

# 完整備份（如需要）
gunzip rg_full_backup.sql.gz
sudo -iu postgres psql -d rg -f rg_full_backup.sql
```

---

## 📂 GitHub 儲存庫

**Repo**：https://github.com/askeywifisit-ui/charter_project

| 資料夾 | 內容 |
|:-------|:-----|
| `packages/` | API, Web, Tools 壓縮檔 |
| `database/` | DB Schema 與備份 |
| `scripts/` | 測試腳本 |
| `docs/` | 完整文件站 |