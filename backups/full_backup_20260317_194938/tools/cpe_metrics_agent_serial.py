#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse, json, subprocess, time, urllib.request, sys, re, os

# optional: global serial mute helper
try:
    import serial_mute
except Exception:
    serial_mute = None
from serial_lock import acquire as serial_lock

CONSOLE_TOOL = "/home/da40/charter/tools/cpe_console_serial.py"

def run_console_command(device, baud, user, password, cmd, timeout=12.0):
    base = [CONSOLE_TOOL, "--device", device, "--baud", str(baud), "--user", user, "--no-lock"]
    if password:
        base += ["--password", password]
    p = subprocess.run(base + ["shell", cmd], capture_output=True, text=True, timeout=timeout)
    if p.returncode == 0:
        return (p.stdout or "").strip()
    raise RuntimeError(p.stderr.strip() or f"console command failed: {cmd}")


def get_node_id(device, baud, user, password):
    """Return plain node id string via AWLAN_Node.id.
    Raise RuntimeError if node id cannot be obtained.
    """
    out = run_console_command(
        device, baud, user, password,
        "ovsh s -r AWLAN_Node -c id 2>/dev/null"
    )
    if not out.strip():
        out = run_console_command(
            device, baud, user, password,
            "ovsh s AWLAN_Node id 2>/dev/null"
        )

    m = re.search(r'\b([0-9a-f]{10,})\b', out, re.I)
    if not m:
        # 這裡直接視為錯誤，不要回空字串
        raise RuntimeError("failed to read node-id from console output")

    return m.group(1).lower()


def get_wan_ipv4(device, baud, user, password, iface="br-wan"):
    out = run_console_command(device, baud, user, password, f"ip addr show {iface}")
    m = re.search(r"\binet (?!6)([0-9]{1,3}(?:\.[0-9]{1,3}){3})", out)
    return m.group(1) if m else None

def get_wifi_band_counters(device, baud, user, password):
    cmd = [CONSOLE_TOOL, "--device", device, "--baud", str(baud), "--user", user, "--no-lock"]
    if password:
        cmd += ["--password", password]
    p = subprocess.run(cmd + ["wifi-bands"], capture_output=True, text=True, timeout=12.0)
    if p.returncode == 0:
        try: return json.loads(p.stdout.strip() or "{}")
        except Exception: return {}
    raise RuntimeError(p.stderr.strip() or "wifi-bands failed")

def run_tool_metrics(device, baud, user, password, iface, ping, temp_cmd, with_wifi=False, with_radio=False, retries=1):
    cmd = [CONSOLE_TOOL, "--device", device, "--baud", str(baud), "--user", user, "--no-lock"]
    if password:
        cmd += ["--password", password]
    if temp_cmd:
        cmd += ["--temp-cmd", temp_cmd]
    if with_wifi:
        cmd += ["--with-wifi"]
    if with_radio:
        cmd += ["--with-radio"]
    cmd += ["--iface", iface, "--ping", ping, "metrics"]

    last_err = None
    for _ in range(retries + 1):
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if p.returncode == 0:
            return json.loads(p.stdout.strip() or "{}")
        last_err = p.stderr.strip() or f"tool failed rc={p.returncode}"
        time.sleep(0.6)
    raise RuntimeError(last_err)

def post_json(url, obj, timeout=5):
    data = json.dumps(obj).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        r.read()

def main():
    ap = argparse.ArgumentParser(description="Serial metrics agent → API")
    ap.add_argument("--api", default="http://127.0.0.1:8080")
    ap.add_argument("--device", default="/dev/ttyUSB0")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--user", default="root")
    ap.add_argument("--password", default=None)
    ap.add_argument("--iface", default="br-wan")
    ap.add_argument("--ping", default="8.8.8.8")
    ap.add_argument("--temp-cmd", default=None)
    ap.add_argument("--interval", type=float, default=5.0)
    ap.add_argument("--run-id", type=int, default=None)
    ap.add_argument("--device-id", default="cpe-1")
    ap.add_argument("--with-wifi", action="store_true")
    ap.add_argument("--with-radio", action="store_true")
    ap.add_argument("--cmd", choices=["metrics","ipv4","wifi","radio","wifi-bands","node-id"], default="metrics")
    ap.add_argument("--once", action="store_true", help="metrics: 取一次並輸出純 JSON 後退出")
    args = ap.parse_args()

    if not args.password:
        args.password = os.environ.get("CPE_PASSWORD") or os.environ.get("CPE_PASS")

    push_url = args.api.rstrip("/") + "/api/metrics/push"

    if args.cmd == "ipv4":
        with serial_lock(block=True, timeout=10):
            ipv4 = get_wan_ipv4(args.device, args.baud, args.user, args.password, args.iface)
        print(json.dumps({"wan_ipv4": ipv4 or "(none)"})); return

    if args.cmd == "wifi":
        with serial_lock(block=True, timeout=10):
            out = run_console_command(args.device, args.baud, args.user, args.password,
                                      "ovsh s Wifi_Associated_Clients -c mac -r connected==true")
        print(out); return

    if args.cmd == "radio":
        with serial_lock(block=True, timeout=10):
            out = run_console_command(args.device, args.baud, args.user, args.password,
                                      "ovsh s Wifi_Radio_State -c if_name,channel,tx_power")
        print(out); return

    if args.cmd == "wifi-bands":
        with serial_lock(block=True, timeout=10):
            bands = get_wifi_band_counters(args.device, args.baud, args.user, args.password)
        print(json.dumps(bands, ensure_ascii=False)); return

   
    if args.cmd == "node-id":
        try:
            # Bonus hardening: if serial is muted, fail fast with a clear reason
            if serial_mute and hasattr(serial_mute, 'left_seconds'):
                left = int(serial_mute.left_seconds())
                if left > 0:
                    raise RuntimeError(f'serial muted (left={left}s)')

            with serial_lock(block=True, timeout=10):
                nid = get_node_id(args.device, args.baud, args.user, args.password)
        except Exception as e:
            # 失敗時，stderr 印錯誤，並用非 0 結束
            print(f"[node-id] error: {e}", file=sys.stderr)
            sys.exit(1)

        print(nid)
        return


    if args.cmd == "metrics" and args.once:
        with serial_lock(block=True, timeout=10):
            m = run_tool_metrics(args.device, args.baud, args.user, args.password,
                                 args.iface, args.ping, args.temp_cmd,
                                 with_wifi=args.with_wifi, with_radio=args.with_radio,
                                 retries=0)
        print(json.dumps(m, ensure_ascii=False)); return

    while True:
        try:
            with serial_lock(block=True, timeout=10):
                m = run_tool_metrics(args.device, args.baud, args.user, args.password,
                                     args.iface, args.ping, args.temp_cmd,
                                     with_wifi=args.with_wifi, with_radio=args.with_radio,
                                     retries=1)
                m["device_id"] = args.device_id
                if args.run_id is not None:
                    m["run_id"] = args.run_id
                print("[metrics]", json.dumps(m, ensure_ascii=False))
                try: post_json(push_url, m, timeout=5)
                except Exception as e:
                    print("[metrics] push failed:", e, file=sys.stderr)
        except Exception as e:
            print("[metrics] error:", e, file=sys.stderr)
        time.sleep(max(1.0, args.interval))

if __name__ == "__main__":
    main()
