#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""net_probe.py — ping / curl / DNS 測試工具（可綁定來源 IP 或介面）

patched2:
  - DNS：當使用 dig 並綁定來源 IP(-b) 時，若系統 resolver 是 127.0.0.53/127.0.0.1 (systemd-resolved stub)，
    會導致查詢 timeout（因為 loopback DNS 不能用非 loopback source 送出）。
    本版會在 resolver 未指定時，自動為該介面挑一個「非 loopback」DNS：
      1) nmcli 讀 IP4.DNS
      2) 否則 fallback 用該介面 default gateway (常見 CPE 會做 DNS forwarder)
    仍可用 --resolver 強制指定。
"""

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from shutil import which


def run_cmd(cmd: str, timeout=20):
    p = subprocess.run(shlex.split(cmd), capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def get_iface_ip(iface: str, family: str = "4"):
    fam_flag = "-4" if family == "4" else "-6"
    rc, out, _ = run_cmd(f"ip {fam_flag} -o addr show dev {iface}")
    if rc != 0:
        return None
    for line in out.splitlines():
        m = re.search(r"\binet6?\s+([0-9a-fA-F\.:]+)/\d+", line)
        if m:
            return m.group(1)
    return None


def get_iface_gw4(iface: str):
    rc, out, _ = run_cmd(f"ip -4 route show default dev {iface}")
    if rc != 0:
        return None
    # default via 192.168.1.1 dev wlan0 proto dhcp metric 600
    m = re.search(r"\bvia\s+([0-9\.]+)", out)
    return m.group(1) if m else None


def get_nm_dns4(iface: str):
    if not which("nmcli"):
        return None
    rc, out, _ = run_cmd(f"nmcli -g IP4.DNS dev show {iface}")
    if rc != 0:
        return None
    for line in out.splitlines():
        ip = line.strip()
        if ip and re.match(r"^\d+\.\d+\.\d+\.\d+$", ip) and not ip.startswith("127."):
            return ip
    return None


def get_system_nameservers():
    ns = []
    try:
        with open("/etc/resolv.conf", "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                m = re.match(r"nameserver\s+(\S+)", line)
                if m:
                    ns.append(m.group(1))
    except Exception:
        pass
    return ns


def is_loopback_ip(ip: str | None) -> bool:
    if not ip:
        return False
    return ip.startswith("127.") or ip == "::1"


def resolve_src_arg(src_ip: str | None, iface: str | None, ip_family: str = "4") -> str | None:
    if src_ip:
        return src_ip
    if iface:
        return get_iface_ip(iface, ip_family)
    return None


PING_SUMMARY_RE = re.compile(r"(?P<tx>\d+)\s+packets\s+transmitted,\s+(?P<rx>\d+)\s+received.*?(?P<loss>\d+\.?\d*)%.*")
PING_RTT_RE = re.compile(r"(?:rtt|round-trip)\s+min/avg/max/(?:mdev|stddev)\s*=\s*(?P<min>\d+\.?\d*)/(?P<avg>\d+\.?\d*)/(?P<max>\d+\.?\d*)/(?P<mdev>\d+\.?\d*)\s*ms")


def ping_probe(dest="8.8.8.8", src_ip=None, iface=None, count=4, deadline=10, ip_family="4", json_out=False):
    bind = src_ip or iface
    bind_for_ping = bind if bind else ""
    ping_bin = "ping6" if ip_family == "6" else "ping"
    cmd = f"{ping_bin} -c {count} -W 2 -w {deadline}"
    if bind_for_ping:
        cmd += f" -I {bind_for_ping}"
    cmd += f" {dest}"
    rc, out, err = run_cmd(cmd, timeout=max(deadline + 5, 10))

    tx = rx = None
    loss = None
    rtt = {}
    m = PING_SUMMARY_RE.search(out) or PING_SUMMARY_RE.search(err)
    if m:
        tx = int(m.group("tx"))
        rx = int(m.group("rx"))
        loss = float(m.group("loss"))
    m = PING_RTT_RE.search(out) or PING_RTT_RE.search(err)
    if m:
        rtt = {k: float(m.group(k)) for k in ("min", "avg", "max", "mdev")}

    result = {
        "tool": "ping",
        "cmd": cmd,
        "ok": rc == 0 and rx not in (None, 0),
        "rc": rc,
        "dest": dest,
        "bind": bind_for_ping or None,
        "tx": tx,
        "rx": rx,
        "loss_percent": loss,
        "rtt_ms": (rtt or None),
        "stdout": out.strip(),
        "stderr": err.strip(),
    }
    print(json.dumps(result, ensure_ascii=False) if json_out else f"[PING] {dest} -> ok={result['ok']}")
    return result


def curl_probe(url="https://ifconfig.me", src_ip=None, iface=None, max_time=10, method="GET", json_out=False):
    bind = src_ip or iface
    if not which("curl"):
        res = {"tool": "curl", "ok": False, "error": "curl not found"}
        print(json.dumps(res, ensure_ascii=False) if json_out else "[CURL] curl 未安裝")
        return res
    fmt = r"%{http_code} %{time_total} %{remote_ip}"
    cmd = f"curl -sS --max-time {max_time} -o /dev/null -w '{fmt}'"
    if bind:
        cmd += f" --interface {bind}"
    if method.upper() == "HEAD":
        cmd += " -I"
    cmd += f" {url}"
    rc, out, err = run_cmd(cmd, timeout=max_time + 5)
    http_code = time_total = remote_ip = None
    m = re.match(r"(\d{3})\s+([\d\.]+)\s+([0-9a-fA-F\.:]+)", out.strip()) if out else None
    if m:
        http_code, time_total, remote_ip = int(m.group(1)), float(m.group(2)), m.group(3)
    ok = (rc == 0) and (http_code is not None) and (100 <= http_code < 400)
    result = {
        "tool": "curl",
        "cmd": cmd,
        "ok": ok,
        "rc": rc,
        "url": url,
        "bind": bind or None,
        "http_code": http_code,
        "time_total_sec": time_total,
        "remote_ip": remote_ip,
        "stdout": out.strip(),
        "stderr": err.strip(),
    }
    print(json.dumps(result, ensure_ascii=False) if json_out else f"[CURL] {url} -> ok={ok} code={http_code}")
    return result


def dns_probe(name="example.com", qtype="A", resolver=None, src_ip=None, iface=None, json_out=False):
    dig = which("dig")
    nslookup = which("nslookup")
    bind_ip = src_ip or (get_iface_ip(iface, "4") if iface else None)

    # auto resolver selection when using systemd-resolved stub
    auto_resolver = None
    if resolver is None and bind_ip and not is_loopback_ip(bind_ip):
        sys_ns = get_system_nameservers()
        if any(is_loopback_ip(x) for x in sys_ns):
            # Try per-iface DNS first
            if iface:
                auto_resolver = get_nm_dns4(iface)
                if not auto_resolver:
                    auto_resolver = get_iface_gw4(iface)
            resolver = auto_resolver

    if dig:
        base = f"dig +time=2 +tries=1 {name} {qtype} +short"
        if bind_ip:
            base = f"dig +time=2 +tries=1 -b {bind_ip} {name} {qtype} +short"
        if resolver:
            base = base.replace("dig ", f"dig @{resolver} ")
        rc, out, err = run_cmd(base, timeout=8)
        answers = [x.strip() for x in out.splitlines() if x.strip() and not x.startswith(";")]
        ok = rc == 0 and len(answers) > 0
        result = {
            "tool": "dns",
            "impl": "dig",
            "cmd": base,
            "ok": ok,
            "rc": rc,
            "name": name,
            "type": qtype,
            "resolver": resolver or None,
            "auto_resolver": auto_resolver or None,
            "bind": bind_ip or iface or None,
            "answers": answers or None,
            "stdout": out.strip(),
            "stderr": err.strip(),
        }
    elif nslookup:
        base = f"nslookup -type={qtype} {name} {resolver}" if resolver else f"nslookup -type={qtype} {name}"
        rc, out, err = run_cmd(base, timeout=8)
        answers = []
        for line in out.splitlines():
            m = re.search(r"Address(?:\s+\d+)?:\s+([0-9a-fA-F\.:]+)$", line)
            if m:
                answers.append(m.group(1))
        ok = rc == 0 and len(answers) > 0
        result = {
            "tool": "dns",
            "impl": "nslookup",
            "cmd": base,
            "ok": ok,
            "rc": rc,
            "name": name,
            "type": qtype,
            "resolver": resolver or None,
            "auto_resolver": auto_resolver or None,
            "bind": bind_ip or iface or None,
            "answers": answers or None,
            "stdout": out.strip(),
            "stderr": err.strip(),
        }
    else:
        base = f"getent hosts {name}"
        rc, out, err = run_cmd(base, timeout=8)
        answers = [line.split()[0] for line in out.splitlines() if line.strip()]
        ok = rc == 0 and len(answers) > 0
        result = {
            "tool": "dns",
            "impl": "getent",
            "cmd": base,
            "ok": ok,
            "rc": rc,
            "name": name,
            "type": "A",
            "resolver": None,
            "auto_resolver": None,
            "bind": bind_ip or iface or None,
            "answers": answers or None,
            "stdout": out.strip(),
            "stderr": err.strip(),
        }

    print(json.dumps(result, ensure_ascii=False) if json_out else f"[DNS] {name} -> ok={result['ok']}")
    return result


def main():
    ap = argparse.ArgumentParser(description="單獨的 ping / curl / DNS 測試工具（可綁來源 IP 或介面）")
    ap.add_argument("--src-ip", help="綁定來源 IP（優先）")
    ap.add_argument("--iface", help="綁定來源介面（若無 --src-ip，DNS 會嘗試抓該介面 IP）")
    ap.add_argument("--json", action="store_true", help="輸出 JSON 便於機器解析")

    sub = ap.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("ping", help="Ping 測試")
    sp.add_argument("dest", nargs="?", default="8.8.8.8")
    sp.add_argument("-c", "--count", type=int, default=4)
    sp.add_argument("--deadline", type=int, default=10)
    sp.add_argument("--ipv", choices=["4", "6"], default="4")

    sc = sub.add_parser("curl", help="HTTP 測試")
    sc.add_argument("url", nargs="?", default="https://ifconfig.me")
    sc.add_argument("--max-time", type=int, default=10)
    sc.add_argument("--method", choices=["GET", "HEAD"], default="GET")

    sd = sub.add_parser("dns", help="DNS 查詢")
    sd.add_argument("name", nargs="?", default="example.com")
    sd.add_argument("--type", default="A")
    sd.add_argument("--resolver", help="DNS 伺服器，例如 8.8.8.8")

    args = ap.parse_args()

    if args.cmd == "ping":
        src = resolve_src_arg(args.src_ip, args.iface, args.ipv)
        ping_probe(dest=args.dest, src_ip=src, iface=(None if src else args.iface),
                   count=args.count, deadline=args.deadline, ip_family=args.ipv, json_out=args.json)
    elif args.cmd == "curl":
        src = resolve_src_arg(args.src_ip, args.iface, "4")
        curl_probe(url=args.url, src_ip=src, iface=(None if src else args.iface),
                   max_time=args.max_time, method=args.method, json_out=args.json)
    elif args.cmd == "dns":
        src = resolve_src_arg(args.src_ip, args.iface, "4")
        dns_probe(name=args.name, qtype=args.type, resolver=args.resolver,
                  src_ip=src, iface=(None if src else args.iface), json_out=args.json)


if __name__ == "__main__":
    main()
