# 下載交付包

> 本頁提供從 GitHub 下載 Charter 交付包的連結。

> ⚠️ **此 Repo 為 Private，需登入 GitHub 才能下載。**
> 尚未受邀請者，請聯繫專案負責人。

**測試帳號（僅供下載用）：**
- **GitHub ID**：`testcharter`
- **GitHub Password**：`Askey#*c1234`

---

## 📦 交付包下載

### Packages（程式與工具）

| 檔案 | 大小 | 說明 |
|:-----|:----:|:-----|
| [📦 charter_api.tar.gz](https://github.com/askeywifisit-ui/charter_project/releases/download/v1.0.0/charter_api.tar.gz) | ~30MB | API 程式 |
| [📦 charter_web.tar.gz](https://github.com/askeywifisit-ui/charter_project/releases/download/v1.0.0/charter_web.tar.gz) | ~23MB | Web UI 程式 |
| [📦 charter_tools.tar.gz](https://github.com/askeywifisit-ui/charter_project/releases/download/v1.0.0/charter_tools.tar.gz) | ~264KB | 工具腳本 |
| [📦 charter_systemd_units.tar.gz](https://github.com/askeywifisit-ui/charter_project/releases/download/v1.0.0/charter_systemd_units.tar.gz) | ~2KB | Systemd 設定 |

---

## 📥 下載指令

```bash
# 登入 GitHub 後下載
curl -O https://github.com/askeywifisit-ui/charter_project/releases/download/v1.0.0/charter_api.tar.gz
curl -O https://github.com/askeywifisit-ui/charter_project/releases/download/v1.0.0/charter_web.tar.gz
curl -O https://github.com/askeywifisit-ui/charter_project/releases/download/v1.0.0/charter_tools.tar.gz
curl -O https://github.com/askeywifisit-ui/charter_project/releases/download/v1.0.0/charter_systemd_units.tar.gz
```

---

## 📂 解壓縮

```bash
tar -xzf charter_api.tar.gz -C /home/da40/
tar -xzf charter_web.tar.gz -C /home/da40/
tar -xzf charter_tools.tar.gz -C /home/da40/
sudo tar -xzf charter_systemd_units.tar.gz -C /etc/systemd/system/
```

---

## 🗄️ 資料庫

| 檔案 | 大小 | 說明 |
|:-----|:----:|:-----|
| [🗄️ rg_schema_only.sql](https://github.com/askeywifisit-ui/charter_project/raw/main/database/rg_schema_only.sql) | ~14KB | Schema 結構（推薦） |
| [🗄️ rg_full_backup.sql.gz](https://github.com/askeywifisit-ui/charter_project/raw/main/database/rg_full_backup.sql.gz) | ~53MB | 完整備份（含資料） |

```bash
# Schema（推薦）
curl -O https://github.com/askeywifisit-ui/charter_project/raw/main/database/rg_schema_only.sql
sudo -iu postgres psql -d rg -f rg_schema_only.sql
```

---

## 📂 GitHub 儲存庫

**Repo**：https://github.com/askeywifisit-ui/charter_project

**Release**：https://github.com/askeywifisit-ui/charter_project/releases/tag/v1.0.0
