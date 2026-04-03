# 5GNR POC - AMP + Smallcell 測試平台

## 專案概述

使用 AMP (Amplab) 平台控制 5G NR 基站 (Smallcell) 的自動化測試平台。

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

## 環境資訊

### AMP (Amplab)
- **URL**: https://amplab.askeydms.com:42443
- **NBI API Base**: /nbi/
- **認證方式**: HTTP Basic Auth

### 基站設備
- **Model**: SCU2140_N48_N77_N78 (5G SA Femtocell)
- **管理介面**: GUI / SSH / NBI API

### 測試站
- IP: 
- Port: 

## 資料夾結構

```
5gnr_poc/
├── README.md
├── 00_overview/           # 專案概覽
│   └── platform_info.md    # 站台資訊
├── 01_setup/              # 環境設定
│   ├── amp_access.md      # AMP 存取設定
│   └──基站連線.md         # 基站網路設定
├── 02_test_cases/          # 測試案例
│   ├── sanity/            # Sanity 測試
│   └── stability/          # Stability 測試
├── 03_scripts/            # 自動化腳本
│   ├── amp_api/           # AMP NBI API 腳本
│   └──基站控制/          # 基站控制腳本
├── 04_reports/            # 測試報告
└── 05_troubleshooting/    # 疑難排解
```

## API 端點 (AMP NBI)

| 功能 | Method | Endpoint |
|------|--------|----------|
| 驗證 | GET | /nbi/user/accountAdmin/verify |
| 設備資訊 | GET | /nbi/device/generalData/{id}/deviceInfo |
| Reboot | POST | /nbi/device/{id}/reboot |
| Config | GET/PUT | /nbi/device/{id}/config |

## 自動化腳本

### AMP NBI API 腳本
- `noc_api_cli.py` - NOC API 命令列工具
- 支援設備重啟、狀態查詢、組態管理

### 基站控制腳本
- `cpe_ssh.py` - SSH 連線控制
- `cpe_console.py` - Console 序列埠控制

## 聯絡窗口

- PM: 
- RD: 
- QA: 

## 備註

- 建立時間：2026-04-03
- 參考 Charter 測試平台架構
