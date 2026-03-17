#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse, json, time, re, contextlib, os, sys, subprocess
from typing import Optional, List, Dict
import serial
from serial_lock import acquire as serial_lock

PROMPT = b"<<<P>>> "
_MUTE_FILE = "/home/da40/charter/var/serial.mute"  # global mute flag
_MUTE_LOGGED = False  # log mute only once per process

# ----- password helpers (cpe_info + logging) -----
CPE_INFO_BIN = os.environ.get("CPE_INFO_BIN", "cpe_info")


def log(msg: str) -> None:
    """Simple stderr logger for this tool."""
    print(f"[console] {msg}", file=sys.stderr, flush=True)


def get_password_from_cpe_info(timeout: float = 5.0) -> Optional[str]:
    """
    Fetch password via `cpe_info --password` with timeout and error handling.
    Returns the password string on success, or None on failure.
    """
    cmd = [CPE_INFO_BIN, "--password"]
    try:
        p = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=True,  # rc != 0 -> CalledProcessError
        )
    except subprocess.TimeoutExpired:
        log(f"{CPE_INFO_BIN} --password TIMEOUT after {timeout:.1f}s")
        return None
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").strip()
        log(f"{CPE_INFO_BIN} --password FAILED rc={e.returncode}: {stderr}")
        return None

    pw = (p.stdout or "").strip()
    if not pw:
        log(f"{CPE_INFO_BIN} --password returned EMPTY password")
        return None

    # 依你的要求：完整密碼寫進 log（注意安全風險）
    log(f"{CPE_INFO_BIN} --password returned '{pw}'")
    return pw


def resolve_password(args_password: Optional[str]) -> str:
    """
    Unified password resolution logic. Priority:
      1) CLI --password
      2) env CPE_PASSWORD / CPE_PASS
      3) cpe_info --password
    Logs the actual password used and its source.
    """
    if args_password:
        password = args_password
        source = "CLI --password"
    else:
        env_pw = os.environ.get("CPE_PASSWORD") or os.environ.get("CPE_PASS")
        if env_pw:
            password = env_pw
            source = "env(CPE_PASSWORD/CPE_PASS)"
        else:
            password = get_password_from_cpe_info()
            source = CPE_INFO_BIN
            if not password:
                log("ERROR: failed to obtain password from cpe_info --password")
                sys.exit(2)

    log(f"using password '{password}' from {source}")
    return password


def _is_muted() -> bool:
    """Return True if serial is globally muted.

    Bonus hardening:
      - If mute file exists but is already expired, auto-clear it (stale cleanup).
      - When muted, log once to stderr with remaining seconds.
    """
    global _MUTE_LOGGED
    try:
        with open(_MUTE_FILE) as f:
            raw = (f.read() or "0").strip()
        until = float(raw) if raw else 0.0
        now_ts = time.time()
        if now_ts >= until:
            # stale flag: clear it so the next script won't be surprised by a leftover file
            try:
                os.remove(_MUTE_FILE)
            except FileNotFoundError:
                pass
            except Exception:
                pass
            _MUTE_LOGGED = False
            return False

        left = int(max(0.0, until - now_ts))
        if not _MUTE_LOGGED:
            log(f"serial muted (left={left}s) file={_MUTE_FILE}")
            _MUTE_LOGGED = True
        return True
    except FileNotFoundError:
        _MUTE_LOGGED = False
        return False
    except Exception:
        return False

def now() -> float:
    return time.monotonic()

def read_until(ser: serial.Serial, patterns, timeout: float = 5.0) -> bytes:
    if isinstance(patterns, (bytes, bytearray)):
        patterns = [patterns]
    buf = bytearray()
    end = now() + timeout
    while now() < end:
        n = ser.in_waiting
        if n:
            buf += ser.read(n)
            for p in patterns:
                if p in buf:
                    return bytes(buf)
        else:
            time.sleep(0.02)
    return bytes(buf)

def write_line(ser: serial.Serial, s: str):
    if _is_muted():
        return 0
    if not s.endswith("\n"):
        s += "\n"
    ser.write(s.encode("utf-8"))
    ser.flush()
    return 1

def run_cmd(ser: serial.Serial, cmd: str, tout: float = 4.0) -> str:
    if _is_muted():
        return ""
    ser.reset_input_buffer()
    write_line(ser, cmd)
    raw = read_until(ser, PROMPT, timeout=tout)
    txt = raw.decode("utf-8", errors="ignore")
    lines = txt.splitlines()
    if lines and lines[0].strip() == cmd.strip():
        lines = lines[1:]
    if lines and lines[-1].endswith(PROMPT.decode()):
        lines = lines[:-1]
    return "\n".join(lines).strip()

def try_login(ser: serial.Serial, user: str, password: Optional[str], login_timeout: float = 10.0):
    if _is_muted():
        return
    write_line(ser, "")
    out = read_until(ser, [b"login:", b"Login:", b"Password:", PROMPT], timeout=2.0)
    if PROMPT in out or out.strip().endswith((b"#", b"$")):
        write_line(ser, 'export PS1="<<<P>>> " ; stty -echo 2>/dev/null || true')
        read_until(ser, PROMPT, timeout=2.0)
        return
    end = now() + login_timeout
    seen_login = (b"login:" in out or b"Login:" in out)
    while now() < end:
        if seen_login:
            write_line(ser, user)
            out = read_until(ser, [b"Password:", PROMPT], timeout=4.0)
            if b"Password:" in out and password is not None:
                write_line(ser, password)
                out = read_until(ser, PROMPT, timeout=6.0)
            write_line(ser, 'export PS1="<<<P>>> " ; stty -echo 2>/dev/null || true')
            read_until(ser, PROMPT, timeout=2.0)
            return
        else:
            out += read_until(ser, [b"login:", b"Login:", PROMPT], timeout=1.5)
            if b"login:" in out or b"Login:" in out:
                seen_login = True
            elif PROMPT in out:
                return
    raise RuntimeError("login timeout")

# ---------- helpers for metrics ----------
def _read_if_counters(ser: serial.Serial, iface: str):
    txt = run_cmd(ser, "cat /proc/net/dev", 3.0)
    for line in txt.splitlines():
        if f"{iface}:" in line:
            nums = line.split(":", 1)[1].split()
            try:
                return int(nums[0]), int(nums[8])
            except Exception:
                return None, None
    return None, None

def _fix_wrap(delta: Optional[int]) -> int:
    if delta is None: return 0
    if delta < 0: delta += (1 << 32)
    if delta < 0: delta += (1 << 64)
    if delta < 0: delta = 0
    return delta

def net_rate_mbps(ser: serial.Serial, iface: str, sample_sec: float = 1.2):
    t1 = now()
    rx1, tx1 = _read_if_counters(ser, iface)
    time.sleep(sample_sec)
    rx2, tx2 = _read_if_counters(ser, iface)
    dt = max(0.2, now() - t1 - 0.3)
    if None in (rx1, tx1, rx2, tx2):
        return 0.0, 0.0
    dr = _fix_wrap(rx2 - rx1); dtb = _fix_wrap(tx2 - tx1)
    return (dr * 8.0 / dt / 1e6), (dtb * 8.0 / dt / 1e6)

def parse_temp_str(s: str) -> Optional[float]:
    if not s: return None
    s = s.strip().split()[0].replace("°C","").replace("C","")
    try:
        v = float(s)
        return round(v/1000.0, 1) if v > 200 else round(v, 1)
    except Exception:
        return None

def get_temp(ser: serial.Serial, temp_cmd: Optional[str]) -> Optional[float]:
    if temp_cmd:
        out = run_cmd(ser, temp_cmd, 3.5)
        v = parse_temp_str(out)
        if v is not None: return v
    best = None
    for i in range(12):
        out = run_cmd(ser, f"cat /sys/class/thermal/thermal_zone{i}/temp", 1.2)
        v = parse_temp_str(out)
        if v is not None:
            best = v if best is None else max(best, v)
    if best is not None: return best
    out = run_cmd(ser, "sensors 2>/dev/null | awk -F'[+ ]' '/temp1|Package|Tdie/{print $3; exit}'", 3.5)
    return parse_temp_str(out)

def _ovs_raw_macs(ser: serial.Serial, where: str, timeout: float = 5.0) -> str:
    return run_cmd(ser, f"ovsh s -r Wifi_Associated_Clients -w {where} -c mac 2>/dev/null", tout=timeout)

def _extract_macs(text: str):
    macs, seen = [], set()
    for line in text.splitlines():
        m = re.search(r'([0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5})', line)
        if m:
            mac = m.group(1).lower()
            if mac not in seen:
                seen.add(mac); macs.append(mac)
    return macs

def wifi_list_macs(ser: serial.Serial):
    raw = _ovs_raw_macs(ser, "connected==true")
    macs = _extract_macs(raw)
    if not macs:
        raw = _ovs_raw_macs(ser, "state==active")
        macs = _extract_macs(raw)
    return macs

def wifi_count_ovs(ser: serial.Serial) -> int:
    return len(wifi_list_macs(ser))

# Radio parse
RADIO_KEYS = ["if_name", "channel", "ht_mode", "tx_power", "country"]
def _parse_radio_kv_blocks(text: str) -> List[Dict[str, str]]:
    rows, block = [], {}
    for ln in text.splitlines():
        s = ln.strip()
        if not s: continue
        if set(s) == {"-"}:
            if block: rows.append({k: block.get(k, "") for k in RADIO_KEYS}); block = {}
            continue
        m = re.match(r"^([A-Za-z0-9_]+)\s*[:|]\s*(.+?)\s*$", s)
        if m:
            key, val = m.group(1), m.group(2)
            if key in RADIO_KEYS: block[key] = val
    if block: rows.append({k: block.get(k, "") for k in RADIO_KEYS})
    return [r for r in rows if any(v for v in r.values())]

def _parse_radio_raw(text: str) -> List[Dict[str, str]]:
    rows, cur = [], {}
    for ln in text.splitlines():
        s = ln.strip()
        if not s or set(s)=={"-"}: continue
        m = re.match(r"^([A-Za-z0-9_]+)\s*[:|]\s*(.+?)\s*$", s)
        if not m: continue
        key, val = m.group(1), m.group(2)
        if key == "if_name":
            if cur: rows.append({k: cur.get(k, "") for k in RADIO_KEYS}); cur = {}
        if key in RADIO_KEYS: cur[key] = val
    if cur: rows.append({k: cur.get(k, "") for k in RADIO_KEYS})
    return [r for r in rows if any(v for v in r.values())]

def radio_status(ser: serial.Serial) -> List[Dict[str, str]]:
    out_tbl = run_cmd(ser, "ovsh s Wifi_Radio_State -T -M -c if_name -c channel -c ht_mode -c tx_power -c country 2>/dev/null", 5.0)
    rows = _parse_radio_kv_blocks(out_tbl)
    if rows: return rows
    out_raw = run_cmd(ser, "ovsh s -r Wifi_Radio_State -c if_name,channel,ht_mode,tx_power,country 2>/dev/null", 5.0)
    return _parse_radio_raw(out_raw)

# Per-band station counters
def _count_wlanconfig(ser: serial.Serial, ifname: str, timeout: float = 7.0) -> int:
    """Count associated stations on a given BSS.
    Primary: `wlanconfig <if> list` (lines starting with MAC).
    Fallback: `iw dev <if> station dump` (lines starting with 'Station').
    """
    out = run_cmd(ser, f"wlanconfig {ifname} list", tout=timeout)
    cnt = 0
    for ln in out.splitlines():
        s = ln.strip()
        if not s or s.upper().startswith("ADDR ") or "RSSI is combined" in s:
            continue
        if re.match(r"^[0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5}\s+\d+\s", s):
            cnt += 1
        elif re.match(r"^[0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5}\b", s):
            cnt += 1
    if cnt == 0:
        dump = run_cmd(ser, f"iw dev {ifname} station dump", tout=timeout)
        cnt = len(re.findall(r'(?mi)^Station\s', dump))
    return cnt

def wifi_band_counters(ser: serial.Serial) -> dict:
    if _is_muted():
        return {"24g": None, "5g": None, "6g": None, "total": None, "state": "muted"}
    names = [
        (os.environ.get("CPE_IF_24", "home-ap-24"), "24g"),
        (os.environ.get("CPE_IF_50", "home-ap-50"), "5g"),
        (os.environ.get("CPE_IF_60", "home-ap-60"), "6g"),
    ]
    res = {}
    for ifn, key in names:
        try:
            res[key] = _count_wlanconfig(ser, ifn, timeout=7.0)
        except Exception:
            res[key] = 0
    res["total"] = sum(v for v in res.values() if isinstance(v, int))
    return res

def parse_cpu_stat(txt: str):
    for line in txt.splitlines():
        if line.startswith("cpu "):
            parts = line.split()
            nums = list(map(int, parts[1:8]))
            idle = nums[3] + nums[4]
            return idle, sum(nums)
    return 0, 0

def get_metrics(ser: serial.Serial, iface: str, ping_target: str, temp_cmd: Optional[str]):
    s1 = run_cmd(ser, "cat /proc/stat", 3.0); idle1, total1 = parse_cpu_stat(s1)
    time.sleep(0.5)
    s2 = run_cmd(ser, "cat /proc/stat", 3.0); idle2, total2 = parse_cpu_stat(s2)
    cpu_pct = (1.0 - max(0, idle2 - idle1) / max(1, total2 - total1)) * 100.0

    meminfo = run_cmd(ser, "cat /proc/meminfo", 3.0)
    mt = ma = None
    for line in meminfo.splitlines():
        if line.startswith("MemTotal:"):      mt = int(line.split()[1])
        if line.startswith("MemAvailable:"):  ma = int(line.split()[1])
    mem_pct = (mt - ma) / mt * 100.0 if mt and ma is not None else None

    rx_mbps, tx_mbps = net_rate_mbps(ser, iface, 1.2)

    latency_ms = None
    ping = run_cmd(ser, f"ping -c 3 -w 5 {ping_target}", 7.0)
    for line in ping.splitlines():
        if "rtt min/avg/max" in line or "round-trip min/avg/max" in line:
            seg = line.split("=")[1].split()[0]
            latency_ms = float(seg.split("/")[1]); break
        m = re.search(r"time=([\\d\\.]+)\\s*ms", line)
        if m: latency_ms = float(m.group(1)); break

    temp_c = get_temp(ser, temp_cmd)
    return {
        "cpu_pct": round(cpu_pct, 2),
        "mem_pct": None if mem_pct is None else round(mem_pct, 2),
        "temp_c": None if temp_c is None else temp_c,
        "rx_mbps": round(rx_mbps, 3),
        "tx_mbps": round(tx_mbps, 3),
        "latency_ms": None if latency_ms is None else round(latency_ms, 2),
    }

# --- Added: fetch node id from OVSDB (AWLAN_Node.id) ---
def get_node_id(ser: serial.Serial) -> str:
    """
    Return plain node id string (e.g. 90d3cfeb6a4d).
    Tries raw/column modes for robustness.
    """
    out = run_cmd(ser, "ovsh s -r AWLAN_Node -c id 2>/dev/null", 4.0) or ""
    if not out.strip():
        out = run_cmd(ser, "ovsh s AWLAN_Node id 2>/dev/null", 4.0) or ""
    for ln in out.splitlines():
        m = re.search(r'\\b([0-9a-f]{10,})\\b', ln, re.I)
        if m:
            return m.group(1).lower()
    return out.strip()


def main():
    ap = argparse.ArgumentParser(description="CPE console via RS232 (lock + mute-safe)")
    ap.add_argument("--device", default="/dev/ttyUSB0")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--user", default="root")
    ap.add_argument("--password", default=None)
    ap.add_argument("--iface", default="eth0")
    ap.add_argument("--ping", default="8.8.8.8")
    ap.add_argument("--temp-cmd", default=None)
    ap.add_argument("--login-timeout", type=float, default=10.0)
    ap.add_argument("--read-timeout", type=float, default=0.2)
    ap.add_argument("--no-lock", action="store_true")
    ap.add_argument("--with-wifi", action="store_true")
    ap.add_argument("--with-radio", action="store_true")
    ap.add_argument("cmd", choices=["metrics","wifi-count","wifi-macs","radio-status","shell","wifi-bands","node-id"], nargs="?", default="metrics")
    ap.add_argument("shell_cmd", nargs=argparse.REMAINDER)
    args = ap.parse_args()

    # 使用統一的密碼解析邏輯（CLI / env / cpe_info）
    args.password = resolve_password(args.password)

    cm = contextlib.nullcontext() if args.no_lock else serial_lock(block=True, timeout=30)
    with cm:
        ser = serial.Serial(args.device, args.baud, timeout=args.read_timeout)
        try:
            try_login(ser, args.user, args.password, args.login_timeout)

            if args.cmd == "metrics":
                m = get_metrics(ser, args.iface, args.ping, args.temp_cmd)
                if args.with_wifi:
                    m["wifi_clients"] = wifi_count_ovs(ser)
                    try: m["wifi_bands"] = wifi_band_counters(ser)
                    except Exception: pass
                if args.with_radio:
                    m["radio"] = radio_status(ser)
                print(json.dumps(m, ensure_ascii=False))

            elif args.cmd == "wifi-count":
                print(wifi_count_ovs(ser))

            elif args.cmd == "wifi-macs":
                for mac in wifi_list_macs(ser):
                    print(mac)

            elif args.cmd == "radio-status":
                print(json.dumps(radio_status(ser), ensure_ascii=False))

            elif args.cmd == "shell":
                cmd_str = " ".join(args.shell_cmd).strip()
                if not cmd_str:
                    raise RuntimeError("no shell command provided (usage: ... shell <cmd>)")
                out = run_cmd(ser, cmd_str, tout=8.0)
                print(out)

            elif args.cmd == "wifi-bands":
                data = wifi_band_counters(ser)
                print(json.dumps(data, ensure_ascii=False))

            elif args.cmd == "node-id":
                nid = get_node_id(ser)
                print(nid)

        finally:
            try: ser.close()
            except Exception: pass

if __name__ == "__main__":
    main()

