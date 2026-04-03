# Factory Reset GUI Skill

## 詳細步驟

### Step 1：細胞 GUI Factory Reset（headless Playwright）

1. 登入細胞 GUI
2. System Settings → Reset
3. 點擊 btn_reset 按鈕（JS）
4. 點擊第一個可見的 OK（WARNING）
5. 點擊第一個可見的 OK（確認）
6. 截圖並細胞重啟

---

### Step 2：確認細胞重啟

- SSH uptime < 3 min

---

### Step 3：修改 Provision Method = Remote + Management Server（GUI）

- 頁面：/configuration/gNB
- 點擊第一個可見的 OK（確認）
- 選擇 Remote
- 設定 Management Server = https://amplab.sbi.askeydms.com:42443/cwmp
- 按 Save

---

### Step 4：Reboot（SSH）

- ssh reboot

---

### Step 5：確認 Management Server（SSH）

- 驗證設定正確

---

### Step 6：等待 GPS Sync（約 7 分鐘）

---

### Step 7：每 90 秒檢查 GPS 直到 DISP

- 截圖 GPS status

---

## Notes

- 適用於 5G SA Femtocell (SCU2140_N48_N77_N78)
- Management Server: https://amplab.sbi.askeydms.com:42443/cwmp
