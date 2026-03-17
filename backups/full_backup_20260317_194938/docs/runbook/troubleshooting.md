# 故障排除

## 1) UI 有開但 run 一直 queued
- 看 worker 是否 idle：`GET /api/runs/worker/status`

## 2) 脚本 fail 在 precondition：noc-context timeout
症狀常見：
- `HTTPSConnectionPool(...): Read timed out (read timeout=20)`

處理方向：
- 確認 Control PC 到 NOC endpoint 網路可達
- 增加 retry/backoff（腳本或 wrapper）
- 視情況拉長 timeout（避免尖峰時段 flakiness）

## 3) API set 成功但 CPE 端表未同步
- 屬 eventual consistency
- 用 wait/poll 等待 CPE reserved/leased table 出現再 assert

## 4) Wi‑Fi / route / iface 相關問題（測試機網路面）
常見症狀：
- 腳本需要指定「從哪個介面走 LAN / Wi‑Fi / ping」但環境不同，介面名稱不一致（例如 `eno2` / `en1` / `wlan0`）。
- IPv6 link-local URL 需要 zone id（`%25<iface>`）但拿到的 iface 不對。

處理方向（原則）：
- **先確認本機介面名稱**（control PC 上）：
  - `ip a`（Linux）或 `ifconfig`（macOS）
- 需要帶 zone id 的 IPv6 LLA URL：確認用的是「連到 LAN 的那張網卡」。
- 若腳本有提供 env（例如 `PING_IFACE` / `LAN_SCOPE_IFACE` / `WIFI_IFACE`），以 **systemd 環境或 `.secrets/dut.env`** 集中管理，避免寫死在 script zip。

## 5) OAuth / Token / provider（OpenClaw）
常見症狀：
- Dashboard 打得開，但 `/chat` 顯示：`requires device identity (use HTTPS or localhost)`
- Gateway 需要 token（或 token file）才能讓其他 client 連線。

處理方向：
- **demo/內網最快解**：用 SSH tunnel，把遠端 gateway 映射到本機 `127.0.0.1` 再開 `/chat`。
- 若要讓內網直接用：需要 **HTTPS**（單純 http + 非 localhost 會被瀏覽器 secure context 擋）。
- token 檔（範例）：`~/.openclaw/gateway.token`（權限 600），並確認 `openclaw gateway status` 顯示 `auth=token`。
