# ssh_awlan_tool.py

SSH AWLAN 工具，用於查詢 AWLAN_Node.id 及 Reboot。

---

## 位置

`/home/da40/charter/tools/ssh_awlan_tool.py`

---

## 功能

- SSH 登入 CPE
- 查詢 AWLAN_Node.id
- Reboot（可選靜音）

---

## 常用指令

```bash
# 查詢 node-id
python3 /home/da40/charter/tools/ssh_awlan_tool.py \
  --host 192.168.1.1 \
  --user operator \
  --password 1234 \
  --cmd node-id

# Reboot（靜音 120 秒）
python3 /home/da40/charter/tools/ssh_awlan_tool.py \
  --host 192.168.1.1 \
  --user operator \
  --password 1234 \
  --cmd reboot \
  --mute-console-secs 120 \
  --mute-with-lock
```

---

## 參數說明

| 參數 | 說明 |
|------|------|
| `--host` | CPE IP |
| `--user` | SSH 帳號 |
| `--password` | SSH 密碼 |
| `--cmd` | 指令（node-id, reboot） |
| `--mute-console-secs` | 靜音秒數 |
| `--mute-with-lock` | 靜音時加鎖 |
