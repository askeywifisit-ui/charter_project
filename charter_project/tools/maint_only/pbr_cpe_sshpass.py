#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse, shlex, subprocess, sys, time
from typing import List, Tuple


def _sshpass_ok():
    return shutil.which("sshpass") is not None

def run(cmd, check=False, timeout=30) -> Tuple[int, str, str]:
    if isinstance(cmd, list):
        cmd_str = " ".join(shlex.quote(x) for x in cmd)
        popen_args = dict(args=cmd, text=True)
    else:
        cmd_str = cmd
        popen_args = dict(args=cmd, shell=True, text=True)
    print(f"[CMD] {cmd_str}")
    p = subprocess.run(**popen_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    out = p.stdout or ""; err = p.stderr or ""
    if out:
        print(out, end="" if out.endswith("\n") else "\n")
    if check and p.returncode != 0:
        raise subprocess.CalledProcessError(p.returncode, cmd_str, out, err)
    return p.returncode, out, err

def iproute_ready(src_ip: str, gw: str, iface: str, probe_ip: str = "8.8.8.8", deadline_sec: float = 1.0) -> bool:
    end = time.time() + deadline_sec
    expect = f"via {gw} dev {iface}"
    ok = False
    while time.time() < end:
        _, out, _ = run(f"ip route get {probe_ip} from {src_ip}", check=False)
        if expect in (out or ""):
            ok = True
            break
        time.sleep(0.1)
    print(f"[PBR] route_ready={ok}")
    return ok

def add_rule(cmd: str): run(cmd, check=False)
def del_rule(cmd: str): run(cmd, check=False)

def pbr_setup(src_ip, iface, gw, subnet, table_id, prio_from, prio_to):
    print(f"[PBR] setup on {iface} src={src_ip} via {gw} table={table_id}")
    # rp_filter（iface 與 all）調鬆
    run(f"sysctl -q -w net.ipv4.conf.{iface}.rp_filter=2", check=False)
    run("sysctl -q -w net.ipv4.conf.all.rp_filter=2", check=False)
    # table routes
    run(f"ip -4 route add table {table_id} {subnet} dev {iface} scope link src {src_ip}", check=False)
    run(f"ip -4 route replace table {table_id} default via {gw} dev {iface}", check=False)
    # rules
    add_rule(f"ip -4 rule add from {src_ip}/32 table {table_id} priority {prio_from}")
    add_rule(f"ip -4 rule add to {subnet} table {table_id} priority {prio_to}")
    # 刷快取 & ARP 預熱
    run("ip route flush cache", check=False)
    run(["ping", "-c", "1", "-W", "1", "-I", str(src_ip), str(gw)], check=False)
    # 就緒檢查
    iproute_ready(src_ip, gw, iface, "8.8.8.8", 1.0)
    run(f"ip route get 8.8.8.8 from {src_ip}", check=False)
    run(f"ip route get 1.1.1.1 from {src_ip}", check=False)

def pbr_teardown(src_ip, iface, subnet, table_id, prio_from, prio_to):
    print(f"[PBR] teardown on {iface} table={table_id}")
    del_rule(f"ip -4 rule del from {src_ip}/32 table {table_id} priority {prio_from}")
    del_rule(f"ip -4 rule del to {subnet} table {table_id} priority {prio_to}")
    run(f"ip -4 route flush table {table_id}", check=False)
    run(f"sysctl -q -w net.ipv4.conf.{iface}.rp_filter=2", check=False)
    run("ip route flush cache", check=False)

def pbr_tests(src_ip, iface, gw):
    run(f"ip rule | grep -E ' {src_ip} | lookup ' || true", check=False)
    run("ip route show table all | sed -n '1,200p'", check=False)
    run(["ping", "-I", str(src_ip), "-c", "4", "-W", "2", str(gw)], check=False)
    run(["ping", "-I", str(src_ip), "-c", "4", "-W", "2", "8.8.8.8"], check=False)
    run(["ping", "-I", str(src_ip), "-c", "4", "-W", "2", "1.1.1.1"], check=False)
    run(["curl", "--silent", "--max-time", "10", "--interface", str(src_ip), "https://ifconfig.me"], check=False)
    run(["curl", "--silent", "--max-time", "10", "--interface", str(src_ip), "http://neverssl.com"], check=False)
    run(["bash","-lc", f"dig +time=2 +tries=1 -b {src_ip} example.com A +short"], check=False)
    run(["bash","-lc", f"dig +time=2 +tries=1 -b {src_ip} @8.8.8.8 www.google.com A +short"], check=False)

def pbr_run_wrapper(args, remainder_cmd: List[str]):
    pbr_setup(args.src_ip, args.iface, args.gw, args.subnet, args.table_id, args.prio_from, args.prio_to)
    try:
        if not remainder_cmd:
            print("[PBR] no command provided after 'run --', nothing to execute.")
            return 0
        print("[PBR] executing:", " ".join(shlex.quote(x) for x in remainder_cmd))
        p = subprocess.run(remainder_cmd)
        return p.returncode
    finally:
        if not args.keep:
            pbr_teardown(args.src_ip, args.iface, args.subnet, args.table_id, args.prio_from, args.prio_to)
        else:
            print("[PBR] keep=1 → skipping teardown.")



def pbr_ssh_wrapper(args, host: str, user: str, port: int, connect_timeout: int,
                    remote_cmd: str, options: str, password: str | None = None):
    """setup PBR -> run system ssh -> (optional) teardown.
    Supports password auth via sshpass when available.
    """
    pbr_setup(args.src_ip, args.iface, args.gw, args.subnet, args.table_id, args.prio_from, args.prio_to)
    try:
        use_sshpass = bool(password) and _sshpass_ok()
        base = [
            "ssh",
            "-p", str(port),
            "-o", f"ConnectTimeout={connect_timeout}",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "LogLevel=ERROR",
        ]
        if not use_sshpass:
            base += ["-o", "BatchMode=yes"]
        if options:
            base += shlex.split(options)
        target = f"{user}@{host}"
        cmd = base + [target, remote_cmd]
        if use_sshpass:
            cmd = ["sshpass", "-p", password] + cmd
        print("[PBR_SSH]", " ".join(shlex.quote(x) for x in cmd))
        rc, out, err = run(cmd, timeout=connect_timeout + 10)
        if out:
            print(out, end="" if out.endswith("\n") else "\n")
        if err:
            print(err, file=sys.stderr, end="" if err.endswith("\n") else "\n")
        return rc
    finally:
        if not args.keep:
            pbr_teardown(args.src_ip, args.iface, args.subnet, args.table_id, args.prio_from, args.prio_to)


def build_parser():
    ap = argparse.ArgumentParser(description="PBR to CPE + tests + auto teardown",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # 全域參數（必須在子命令前）
    ap.add_argument("--src-ip", default="192.168.1.2")
    ap.add_argument("--iface", default="eno2")
    ap.add_argument("--gw", default="192.168.1.1")
    ap.add_argument("--subnet", default="192.168.1.0/24")
    ap.add_argument("--table-id", type=int, default=100)
    ap.add_argument("--prio-from", type=int, default=1000)
    ap.add_argument("--prio-to", type=int, default=1001)
    ap.add_argument("--keep", action="store_true")

    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("setup")
    sub.add_parser("teardown")
    sub.add_parser("tests")
    runp = sub.add_parser("run")
    runp.add_argument("remainder", nargs=argparse.REMAINDER, help="use after '--'")
    
    sshp = sub.add_parser("ssh", help="setup PBR then run system ssh, then teardown")
    sshp.add_argument("--host", required=True, help="SSH target host/IP")
    sshp.add_argument("--user", default="operator", help="SSH username")
    sshp.add_argument("--password", default="", help="SSH password (uses sshpass if installed)")
    sshp.add_argument("--port", type=int, default=22, help="SSH port")
    sshp.add_argument("--connect-timeout", type=int, default=15, help="ssh ConnectTimeout seconds")
    sshp.add_argument("--remote-cmd", default="echo SSH_OK", help="Remote command to execute")
    sshp.add_argument("--options", default="", help="Extra ssh options string (optional)")

    return ap

def main(argv=None):
    ap = build_parser()
    args = ap.parse_args(argv)
    if args.cmd == "setup":
        pbr_setup(args.src_ip, args.iface, args.gw, args.subnet, args.table_id, args.prio_from, args.prio_to); return 0
    if args.cmd == "teardown":
        pbr_teardown(args.src_ip, args.iface, args.subnet, args.table_id, args.prio_from, args.prio_to); return 0
    if args.cmd == "tests":
        pbr_tests(args.src_ip, args.iface, args.gw); return 0
    if args.cmd == "run":
        rem = list(args.remainder or [])
        if rem and rem[0] == "--": rem = rem[1:]
        return pbr_run_wrapper(args, rem)
    if args.cmd == "ssh":
        return pbr_ssh_wrapper(args, host=args.host, user=args.user, port=args.port, connect_timeout=args.connect_timeout, remote_cmd=args.remote_cmd, options=args.options, password=args.password)
    ap.print_help(); return 1

if __name__ == "__main__":
    sys.exit(main())

