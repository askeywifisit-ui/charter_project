# 使用者指南

本指南幫助你快速上手 Charter 測試平台。

---

## 常用操作

| 任務 | 快速連結 |
|------|----------|
| 執行測試 | [Runs 操作](runs/) |
| 匯入腳本 | [腳本管理](scripts/) |
| 修改腳本 | [修改腳本](modify_script_code/) |
| 新建腳本 | [建立新腳本](create_new_script/) |

---

## 第一次使用？

### 1. 開啟平台

- **Web UI**：http://172.14.1.140:5173
- **API**：http://172.14.1.140:5173/api

### 2. 執行第一個測試

1. 從 [Sanity 腳本列表](/test_suites/sanity/) 找一個腳本
2. 用 API 執行：
```bash
curl -X POST "http://172.14.1.140:5173/api/scripts/<SCRIPT_ID>/run"
```
3. 看結果：
```bash
curl "http://172.14.1.140:5173/api/runs/<RUN_ID>/log"
```

### 3. 常見問題

- **Import 失敗？** → 檢查 ZIP 內是否有 `main.py`、`manifest.yaml`、`requirements.txt`
- **Run 卡住？** → 檢查 Worker 狀態：`/api/runs/worker/status`
- **需要幫助？** → 聯絡 DA40 團隊

---

## 快速指令

```bash
# 設定
export BASE="http://172.14.1.140:5173"

# 執行腳本
curl -X POST "$BASE/api/scripts/<ID>/run"

# 查看結果
curl "$BASE/api/runs/<ID>/log"

# 匯入腳本
curl -X POST "$BASE/api/scripts/import2" -F "file=@./script.zip"

# 清理舊資料
curl -X DELETE "$BASE/api/runs/purge?older_than_days=0"
```

---

## 完整文件

- [腳本管理](scripts/) - 匯入/匯出/刪除
- [修改腳本](modify_script_code/) - 如何改現有腳本
- [建立新腳本](create_new_script/) - 從頭新建腳本
- [Runs 操作](runs/) - 執行與取證
- [Tools 工具](/tools/index/) - 工具使用說明
