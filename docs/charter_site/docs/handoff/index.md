# Hand-off / 交付（同事照做版）

本章目標：把 Charter 平台交付給「其他同事 / 另一個 lab」時，對方只要照步驟做，就能 **安裝完成 → service 長駐 → 跑通 sanity**。

> 原則：文件站不放任何 NOC email/password；敏感值走 `.secrets/`。

---

## 一頁式 Checklist（建議照順序）

1) **下載交付物**（scripts/web/api；tools 由內部管道）
2) **照安裝頁完成 systemd 長駐**（reboot 後會自動恢復）
3) **填 `.secrets/` 與環境表**（網卡、CPE、NOC profile、customer id）
4) **健康檢查**（API / worker / UI）
5) **跑 1 個 sanity**，抓 log 當 evidence

---

## 相關頁面（照這個順序看）

1) 下載
- [交付下載（GitHub links）](downloads.md)

2) 安裝（platform）
- [平台安裝 / 移植（systemd）](../getting_started/platform_install.md)
- [Quick Start（10 分鐘確認）](../getting_started/quick_start.md)

3) 填環境
- [交付環境表（對方要填）](handoff_env_form.md)
- [Network iface 指南（常踩雷）](network_iface_guide.md)
- [NOC profile / secrets（放哪裡、權限）](noc_profile_secrets.md)

4) 驗證
- [驗證步驟（快速驗證）](handoff_validation.md)

5) scripts 搬移/更新
- [Scripts 移植/匯入規則（同名先刪再匯入）](migration_scripts.md)

---

## 交付包建議內容（對方應該拿到什麼）

- Web（tar.gz）
- API（tar.gz）
- Scripts（sanity/stability zip + manifest）
- systemd units（*.service/*.timer + drop-in）
- 文件站（mkdocs source）
- Tools（tar.gz；**不公開 link**，走內部管道）

> secrets（NOC / SSH / Warehouse 等）不要放在交付包或文件站；請讓對方自行填 `.secrets/`。
