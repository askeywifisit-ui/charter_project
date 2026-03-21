# HEARTBEAT — 定期健康檢查（每 30 分鐘）

## 檢查項目

### 1. 三個 OpenClaw 存活檢查
用 curl probe 確認以下三個 Gateway 可達：
- **Lina（DA40）**：http://localhost:18789（本機）
- **Alice（100.40.1.115）**：http://100.40.1.115:18789
- **Lina_Bot（100.40.1.209）**：http://100.40.1.209:18789

只要任何一個 `Reachable: no`，就列入回報。

### 2. Charter 測試站（11F_140）
檢查：http://172.14.1.140:5173 是否可連線（GET /api/status 或 GET /）

### 3. 對外網路品質
執行 speedtest（`speedtest-cli --simple 2>/dev/null` 或 `curl -s https://speed.cloudflare.com/`），回報下載/上傳延遲。

---

## 回報格式

正常時回報：
```
✅ OpenClaw 存活：Lina ✅ / Alice ✅ / Vega ✅
✅ Charter 站：可連線
🌐 網路：下載 XXX Mbps / 上傳 YYY Mbps / 延遲 ZZZ ms
```

異常時回報：
```
⚠️ OpenClaw 異常：Lina ❌（或「Vega ❌」等）
⚠️ Charter 站：無法連線
🌐 網路：無法測速
```

異常時主動通知，平時安靜。
