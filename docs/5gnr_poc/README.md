# 5GNR POC - AMP + Smallcell 測試平台

## 專案概述

使用 AMP (Amplab) 平台控制 5G NR 基站 (Smallcell) 的自動化測試平台。

## 基站資訊

| 項目 | 內容 |
|------|------|
| **Serial** | E1F8V000957 |
| **Band** | N77 |
| **IP** | 172.14.1.19 |
| **MAC** | F4:52:46:6D:5B:53 |
| **Type** | Orion |
| **GUI Password** | `AskNodeB5B53` (AskNodeB+MAC末2碼) |
| **Management Server** | https://amplab.sbi.askeydms.com:42443/cwmp |

---

## AMP (Amplab) 平台

| 項目 | 內容 |
|------|------|
| **URL** | https://amplab.askeydms.com:42443/ |
| **NBI API Base** | /nbi/ |
| **認證方式** | HTTP Basic Auth |

### 帳號

| Username | Password |
|----------|----------|
| alice | #*cda40da40 |
| lina | #*cda40da40 |

---

## 資料夾結構

```
5gnr_poc/
├── README.md
├── 00_overview/
│   └── platform_info.md    # 站台資訊（已更新）
├── 01_setup/              # 環境設定
├── 02_test_cases/          # 測試案例
├── 03_scripts/            # 自動化腳本
├── 04_reports/            # 測試報告
└── 05_troubleshooting/    # 疑難排解
```

---

## 系統架構

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   AMP UI    │────▶│  NBI API    │────▶│  Smallcell  │
│ (Web/手動)  │     │  (自動化)   │     │   (基站)    │
└─────────────┘     └─────────────┘     └─────────────┘
                          │
                    ┌─────┴─────┐
                    │ Charter   │
                    │   Bot     │
                    └───────────┘
```

---

## 自動化腳本

### AMP NBI API 驗證

```bash
curl -u "alice:#*cda40da40" \
  "https://amplab.askeydms.com:42443/nbi/user/accountAdmin/verify"
```

---

## 備註

- 建立時間：2026-04-03
- 參考 Charter 測試平台架構
