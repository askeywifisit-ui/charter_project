
#!/usr/bin/env python3

import sys, time, re, json, argparse
try:
    import serial  # pyserial
except ImportError:
    print("ERROR: pyserial not installed. Try: pip install pyserial", file=sys.stderr)
    sys.exit(2)

PROMPTS = [b"login:", b"Password:", b"# ", b"$ "]

def read_until(ser, targets, timeout=8.0):
    end = time.time() + timeout
    buf = b""
    while time.time() < end:
        n = ser.in_waiting
        if n:
            chunk = ser.read(n)
            buf += chunk
            for t in targets:
                if t in buf:
                    return buf
        time.sleep(0.05)
    return buf

def send(ser, s):
    if not s.endswith("\n"):
        s = s + "\n"
    ser.write(s.encode())

def login_and_shell(ser, user, password):
    # Wake up
    send(ser, "")
    buf = read_until(ser, [b"login:", b"# ", b"$ "], timeout=5.0)
    if b"login:" in buf:
        send(ser, user)
        buf = read_until(ser, [b"Password:"], timeout=6.0)
        if b"Password:" in buf and password:
            send(ser, password)
        # wait for shell prompt
        read_until(ser, [b"# ", b"$ "], timeout=8.0)
    return True

def run_cmd(ser, cmd, timeout=3.0):
    # clear buffer
    ser.reset_input_buffer()
    send(ser, cmd + " 2>/dev/null")
    time.sleep(0.05)
    buf = read_until(ser, [b"# ", b"$ "], timeout=timeout)
    # strip echoed command and prompt lines
    txt = buf.decode(errors="ignore")
    # Remove the command we sent and split away prompt
    lines = [line for line in txt.splitlines() if not line.strip().endswith(cmd)]
    # Remove prompt-looking tail
    if lines and re.search(r"(# |\$ )$", lines[-1]):
        lines = lines[:-1]
    return "\n".join(lines).strip()

def parse_count(text):
    if not text:
        return 0
    # Sum trailing integers on each line like "home-ap-24: 3"
    total = 0; matched = False
    for line in text.splitlines():
        m = re.search(r"[:\\s]\\s*([0-9]+)\\s*$", line)
        if m:
            matched = True
            total += int(m.group(1))
    if matched:
        return total
    # Fallback: count "Station " lines
    m = re.findall(r"^Station\\s", text, flags=re.M)
    if m:
        return len(m)
    # Try plain int
    try:
        return int(text.strip())
    except Exception:
        return 0

def main():
    ap = argparse.ArgumentParser(description="Count Wi‑Fi stations via RS232 console")
    ap.add_argument("--device", default="/dev/ttyUSB0")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--user", default="root")
    ap.add_argument("--password", default="")
    ap.add_argument("--timeout", type=float, default=8.0)
    args = ap.parse_args()

    ser = serial.Serial(args.device, args.baud, timeout=0.1)
    try:
        login_and_shell(ser, args.user, args.password)
        # 1) list AP VIFs
        vif_txt = run_cmd(ser, "ovsh s -r Wifi_VIF_State -w mode==ap -c if_name", timeout=args.timeout)
        ifaces = [ln.strip() for ln in vif_txt.splitlines() if ln.strip()]
        if not ifaces:
            # fallback common names
            ifaces = ["home-ap-24","home-ap-50","home-ap-6x"]
        # 2) count per iface via iw station dump
        lines = []
        for ifc in ifaces:
            c_txt = run_cmd(ser, f"iw dev {ifc} station dump | grep -c '^Station '", timeout=args.timeout)
            c = 0
            try:
                c = int(c_txt.strip())
            except Exception:
                # fallback: dump & count lines
                dump_txt = run_cmd(ser, f"iw dev {ifc} station dump", timeout=args.timeout)
                c = len(re.findall(r'^Station\\s', dump_txt, flags=re.M))
            lines.append(f"{ifc}: {c}")
        out = "\n".join(lines)
        print(parse_count(out))
    finally:
        try:
            ser.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()
