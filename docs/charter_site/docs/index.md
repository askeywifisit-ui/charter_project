# Charter 測試平台

> 讓你 10 分鐘內跑完第一個測試

---

## 🎯 第一步：執行測試

還沒跑過測試？從這裡開始：

1. **開啟平台** → http://172.14.1.140:5173
2. **找腳本 ID** → [Sanity 腳本列表](test_suites/sanity/)
3. **執行** → `curl -X POST "http://172.14.1.140:5173/api/scripts/<ID>/run"`
4. **看結果** → [如何看測試結果](user_guide/runs/)

---

## 📋 常用功能

| 任務 | 連結 |
|------|------|
| **跑測試** | [Sanity 腳本](test_suites/sanity/) · [Stability 腳本](test_suites/stability/) |
| **怎麼看結果？** | [Runs 操作](user_guide/runs/) |
| **怎麼匯入腳本？** | [腳本管理](user_guide/scripts/) |
| **工具怎麼用？** | [Tools 列表](tools/index/) |
| **平台挂了怎麼辦？** | [Debug 排查](runbook/troubleshooting/) |

---

## 🔧 系統資訊

| 項目 | 值 |
|------|-----|
| Web UI | http://172.14.1.140:5173 |
| API | http://172.14.1.140:5173/api |
| 文件站 | http://172.14.1.140:8000 |

---

## 📚 完整文件（需要時再看）

### 環境架設
- [平台安裝](getting_started/platform_install/)
- [環境參數](environment_template/)
- [交接文件](handoff/index/)

### 腳本操作
- [修改腳本](user_guide/modify_script_code/)
- [新建腳本](user_guide/create_new_script/)

### 參考
- [API 文件](api_reference/)
- [系統拓撲](architecture/topology/)
- [OpenClaw 設定](openclaw_setup/openclaw_test_assistant_setup/)
