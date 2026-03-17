# cpe_console

CPE Console 存取工具。

---

## 位置

`/home/da40/charter/tools/cpe_console`

---

## 功能

- 透過 Serial 存取 CPE Console
- 取得 CPE Serial Number 作為密碼
- 互動式終端機

---

## 使用方式

```bash
# 直接執行（需要 Serial 設備）
/home/da40/charter/tools/cpe_console <DEVICE>
```

---

## 環境變數

| 變數 | 說明 | 預設值 |
|------|------|--------|
| `BAUD` | 鮑率 | 115200 |
| `LOGIN` | 登入帳號 | root |
| `PROMPT_TAG` | 提示標籤 | SBE1V1K |
| `WEB_URL` | CPE Web URL | https://192.168.1.1/cgi-bin/index.cgi |
