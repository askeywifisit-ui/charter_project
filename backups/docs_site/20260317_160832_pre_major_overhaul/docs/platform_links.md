# Platform Links（平台入口 / 常用連結）

這頁整理的是 **Charter 測試平台** 的入口與常用連結。

## Charter 測試平台（Control PC）

- Web UI：`http://<CONTROL_PC_IP>:5173`
- API：同源 `/api/...`（由 UI 呼叫）

> 預設 Control PC（11F_140）：`172.14.1.140`

## 文件站（教學手冊呈現 / TryCloudflare quick tunnel）

> 文件站只是教學手冊的呈現方式；內容主體仍是 Charter 測試平台的 SOP/資料。
>
> TryCloudflare quick tunnel 會不定期變更網址；若你看到 **Error 1033**，通常代表 tunnel 已換新 URL。

- 公網入口（若此頁沒更新，請到文件站主機執行 `/Users/csit/bin/start_charter_docs.sh`，它會印出最新 URL）：
  - **(last known)** https://ron-titled-andrew-opened.trycloudflare.com

- 本機預覽（文件站主機）：<http://127.0.0.1:8000/>

## 相關

- Getting Started：<./getting_started/quick_start/>
- Platform Install (systemd)：<./getting_started/platform_install/>
