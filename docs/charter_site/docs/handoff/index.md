# Hand-off / 外部單位交付（Deployment Checklist）

本章提供把 Charter 平台交付給「其他單位/另一個 Lab」時，**可照做的 checklist**。

> 目標：讓對方在不知道你們內部細節的情況下，也能用最短步驟完成環境替換、驗證平台可用、並跑通一個 sanity。

## 交付包建議內容
- 文件站（本 repo / mkdocs）
- scripts 匯出包（含 `manifest.json`）
- tools 包（tar.gz + sha256）
- web/api 包（zip + sha256）
- 交付環境表（下頁）

## 交付流程（高階）
1) 對方填寫環境表（IP/網卡/NOC profile/CPE 資訊）
2) 套用替換（manifest env / 設定檔）
3) 平台驗證（health/scripts/runs/worker）
4) 跑一個 sanity case（並可拉 log / 下載 archive）

## 相關頁面
- [交付下載（GitHub links）](downloads.md)
- [Environment Template（需替換項目）](../environment_template.md)
- [交付環境表（對方要填）](handoff_env_form.md)
- [驗證步驟（快速驗證）](handoff_validation.md)
