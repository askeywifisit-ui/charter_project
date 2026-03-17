#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
verify_lan_macvlan.py
Standalone verifier for lan_macvlan.py (macvlan + netns + DHCP renew).

Example:
  sudo python3 verify_lan_macvlan.py --parent eno2 --mac 02:11:22:33:44:55 --timeout 30
  sudo python3 verify_lan_macvlan.py --parent eno2 --renew --ping 8.8.8.8
  python3 verify_lan_macvlan.py --parent eno2 --renew  # non-root OK if sudo -n works
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from typing import Any, Dict, Optional


def sh(cmd: list[str], timeout: int = 15, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=check)


def have(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def load_lan_macvlan(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"lan_macvlan.py not found: {path}")

    # 用一個不容易撞名的 module name
    mod_name = "_lan_macvlan_under_test"

    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load spec from {path}")

    mod = importlib.util.module_from_spec(spec)

    # ⭐關鍵：先塞進 sys.modules，避免 dataclass / typing 在 import 時炸掉
    sys.modules[mod_name] = mod

    spec.loader.exec_module(mod)  # type: ignore
    return mod


def iface_exists(iface: str) -> bool:
    cp = sh(["ip", "link", "show", "dev", iface], timeout=5, check=False)
    return cp.returncode == 0


def sudo_nopass_ok() -> bool:
    # Works for both root and sudoers; root returns 0 too.
    cp = sh(["sudo", "-n", "true"], timeout=5, check=False)
    return cp.returncode == 0


def dump_host_snapshot(parent: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    out["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
    out["user"] = {"uid": os.getuid(), "euid": os.geteuid(), "whoami": sh(["whoami"]).stdout.strip()}
    out["pwd"] = os.getcwd()
    out["python"] = sys.executable
    out["have"] = {
        "ip": have("ip"),
        "sudo": have("sudo"),
        "dhclient": have("dhclient"),
        "udhcpc": have("udhcpc"),
        "unshare": have("unshare"),
        "ping": have("ping"),
    }
    # interface snapshot
    out["parent"] = parent
    out["parent_exists"] = iface_exists(parent)
    out["ip_br_link"] = sh(["ip", "-br", "link"], timeout=10, check=False).stdout.strip().splitlines()[:40]
    out["ip_addr_parent"] = sh(["ip", "-4", "addr", "show", "dev", parent], timeout=10, check=False).stdout.strip()
    out["ip_route"] = sh(["ip", "route"], timeout=10, check=False).stdout.strip().splitlines()[:50]
    out["sudo_nopass_ok"] = sudo_nopass_ok() if have("sudo") else False
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lan-macvlan-path", default="/home/da40/charter/tools/lan_macvlan.py")
    ap.add_argument("--parent", default="eno2")
    ap.add_argument("--ns", default="auto")
    ap.add_argument("--iface", default="lan_test0")
    ap.add_argument("--mac", default=None, help="e.g. 02:11:22:33:44:55")
    ap.add_argument("--timeout", type=int, default=25, help="DHCP timeout seconds")
    ap.add_argument("--renew", action="store_true", help="do DHCP renew")
    ap.add_argument("--ping", default=None, help="optional ping target inside netns (ip or domain)")
    ap.add_argument("--json", action="store_true", help="print json only")
    args = ap.parse_args()

    result: Dict[str, Any] = {"ok": False, "args": vars(args)}

    # Basic snapshot
    try:
        snap = dump_host_snapshot(args.parent)
        result["host"] = snap
        if not snap["have"]["ip"]:
            raise RuntimeError("missing command: ip")
        if not snap["parent_exists"]:
            raise RuntimeError(f"parent iface not found: {args.parent}")
        if os.geteuid() != 0:
            # lan_macvlan.py uses sudo -n for privileged ops; verify here up-front.
            if not snap["have"]["sudo"]:
                raise RuntimeError("not root and missing sudo command")
            if not snap["sudo_nopass_ok"]:
                raise RuntimeError("sudo -n not permitted (need NOPASSWD sudoers for ip/netns/dhclient)")
        if not snap["have"]["dhclient"] and not snap["have"]["udhcpc"]:
            raise RuntimeError("no DHCP client found: need dhclient or udhcpc")
    except Exception as e:
        result["error"] = f"precheck_failed: {e}"
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 2

    # Load module
    try:
        lm = load_lan_macvlan(args.lan_macvlan_path)
        result["lan_macvlan_loaded"] = {"path": args.lan_macvlan_path, "need_sudo": bool(lm._need_sudo())}
    except Exception as e:
        result["error"] = f"import_failed: {e}"
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 3

    # Run macvlan + dhcp
    try:
        with lm.MacvlanNS(parent_iface=args.parent, ns=args.ns, v_iface=args.iface, mac=args.mac) as mv:
            result["created"] = {
                "ns": mv.ns,
                "iface": mv.v_iface,
                "parent": mv.parent_iface,
                "mac": mv.mac_addr,
            }

            if args.renew:
                info = mv.renew_dhcp(timeout_sec=args.timeout)
                result["dhcp"] = info
                result["ipv4"] = mv.get_ipv4()
                result["default_route"] = lm.get_default_route(mv.ns)
                result["dns"] = mv.get_dns_servers()

            if args.ping:
                # ping needs renew to have addr/route; but allow user to try anyway
                mv.ping(args.ping)
                result["ping"] = {"target": args.ping, "ok": True}

        result["ok"] = True
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("OK")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    except Exception as e:
        result["error"] = f"run_failed: {e}"
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 4


if __name__ == "__main__":
    raise SystemExit(main())

