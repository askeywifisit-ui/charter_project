# 5GNR POC - 站台資訊

## 基站設備 (Smallcell)

| 項目 | 內容 |
|------|------|
| **Serial** | E1F8V000957 |
| **Band** | N77 |
| **IP** | 172.14.1.19 |
| **MAC** | F4:52:46:6D:5B:53 |
| **Type** | Orion |
| **GUI Password** | AskNodeB+MAC末2碼 → `AskNodeB5B53` |
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

## 設備 Internal ID

- **Device Internal ID**: `69c4ac5ced75d28a8cdd1f6e`

---

## NBI API Endpoints

| 功能 | Method | Endpoint |
|------|--------|----------|
| 驗證 | GET | /nbi/user/accountAdmin/verify |
| 設備資訊 | GET | /nbi/device/generalData/{id}/deviceInfo |
| 設備清單 | GET | /nbi/device/devices |
| Reboot | POST | /nbi/device/{id}/reboot |
| Config | GET/PUT | /nbi/device/{id}/config |

---

## 驗證方式

```bash
curl -u "alice:#*cda40da40" \
  "https://amplab.askeydms.com:42443/nbi/user/accountAdmin/verify"
```
