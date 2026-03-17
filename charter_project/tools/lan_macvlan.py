#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
lan_macvlan.py
Create a macvlan interface with a unique MAC under a network namespace,
renew DHCP inside the namespace, and clean up safely.

Key features:
- Works with ISC dhclient 4.4.1 (no -timeout): uses subprocess timeout instead.
- Extracts DNS servers from dhclient lease, and can ping domain names inside netns
  even when host uses systemd-resolved stub (127.0.0.53).
- Non-root supported via `sudo -n` for privileged ops (requires NOPASSWD sudoers).

Example:
  sudo python3 lan_macvlan.py --parent eno2 --renew --ping google.com --json
"""

from __future__ import annotations

import json
import os
import re
import secrets
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Tuple


class CmdError(RuntimeError):
    pass


# ---------------------------
# Privilege helpers
# ---------------------------

def _is_root() -> bool:
    return os.geteuid() == 0


def _need_sudo() -> bool:
    return not _is_root()


def _sudo_prefix() -> List[str]:
    return ["sudo", "-n"]


def _run(
    args: List[str],
    check: bool = True,
    capture: bool = True,
    text: bool = True,
    timeout: Optional[int] = None,
    sudo: bool = False,
) -> subprocess.CompletedProcess:
    cmd = args
    if sudo and _need_sudo():
        cmd = _sudo_prefix() + args

    try:
        cp = subprocess.run(
            cmd,
            check=False,
            capture_output=capture,
            text=text,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        raise CmdError(f"cmd timeout after {timeout}s: {' '.join(cmd)}") from e

    if check and cp.returncode != 0:
        raise CmdError(
            f"cmd failed ({cp.returncode}): {' '.join(cmd)}\nstdout={cp.stdout}\nstderr={cp.stderr}"
        )
    return cp


def _have(cmd: str) -> bool:
    return shutil.which(cmd) is not None


# ---------------------------
# Netns + link helpers
# ---------------------------

def _iface_exists(iface: str) -> bool:
    try:
        _run(["ip", "link", "show", "dev", iface], check=True, sudo=False)
        return True
    except CmdError:
        return False

def gen_unique_iface(prefix: str = "lan", max_len: int = 15, attempts: int = 30) -> str:
    """Generate a short, host-safe, currently-unused interface name.

    Notes:
      - Linux ifname is typically limited to 15 chars.
      - We check existence on the host namespace because macvlan is created on host first.
    """
    prefix = re.sub(r"[^a-zA-Z0-9_]", "", (prefix or "lan"))
    # Reserve space for an 8-char suffix (pid+rand); keep prefix short
    prefix = prefix[: max(1, min(6, max_len - 8))]

    for _ in range(attempts):
        suffix = f"{os.getpid() % 10000:04d}{secrets.token_hex(2)}"
        name = (prefix + suffix)[:max_len]
        if not _iface_exists(name):
            return name

    raise CmdError("failed to allocate a unique iface name; please pass --iface explicitly")



def detect_parent_iface(prefer: Optional[List[str]] = None) -> str:
    prefer = prefer or ["eno2", "ens19"]
    for i in prefer:
        if _iface_exists(i):
            return i
    raise CmdError(f"no parent iface found in {prefer}. Please pass parent_iface explicitly.")


def gen_local_admin_mac() -> str:
    b = bytearray(secrets.token_bytes(6))
    b[0] = 0x02  # locally administered, unicast
    return ":".join(f"{x:02x}" for x in b)


def normalize_mac(mac: str) -> str:
    mac = mac.strip().lower()
    if "-" in mac:
        mac = mac.replace("-", ":")
    if ":" not in mac and len(mac) == 12:
        mac = ":".join(mac[i:i + 2] for i in range(0, 12, 2))
    parts = mac.split(":")
    if len(parts) != 6 or any(len(p) != 2 for p in parts):
        raise ValueError(f"invalid mac format: {mac}")
    int("".join(parts), 16)
    return mac


def _ip_netns_exec(ns: str, cmd: List[str], timeout: Optional[int] = None) -> subprocess.CompletedProcess:
    # ip netns exec requires CAP_NET_ADMIN
    return _run(["ip", "netns", "exec", ns] + cmd, check=True, timeout=timeout, sudo=True)


def _netns_exists(ns: str) -> bool:
    cp = _run(["ip", "netns", "list"], check=True, sudo=True)
    return any(line.split()[0] == ns for line in cp.stdout.splitlines() if line.strip())


def ensure_netns(ns: str) -> None:
    if not _netns_exists(ns):
        _run(["ip", "netns", "add", ns], check=True, sudo=True, timeout=10)
    _ip_netns_exec(ns, ["ip", "link", "set", "lo", "up"], timeout=10)


def netns_pids(ns: str) -> List[int]:
    """Return PIDs currently in the given named netns."""
    cp = _run(["ip", "netns", "pids", ns], check=False, sudo=True)
    pids: List[int] = []
    for line in (cp.stdout or "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            pids.append(int(line))
        except ValueError:
            continue
    return pids


def _kill_pid(pid: int, sig: int) -> None:
    """Best-effort kill for a PID. Uses sudo when not root."""
    try:
        if _is_root():
            os.kill(pid, sig)
        else:
            _run(["kill", f"-{sig}", str(pid)], check=False, sudo=True, timeout=5)
    except ProcessLookupError:
        return
    except PermissionError:
        return
    except CmdError:
        return


def kill_netns_pids(ns: str, grace_sec: float = 1.0) -> None:
    """Kill processes living in the named netns to avoid leaving unnamed netns behind."""
    pids = netns_pids(ns)
    if not pids:
        return

    for pid in pids:
        _kill_pid(pid, 15)

    try:
        import time
        time.sleep(grace_sec)
    except Exception:
        pass

    for pid in pids:
        _kill_pid(pid, 9)


def find_mac_holders(mac: str, max_hits: int = 10) -> List[Dict[str, str]]:
    """Find processes/netns holding a given MAC (best-effort).

    This detects *unnamed* network namespaces too, via lsns + nsenter.
    Returns list of dicts: {"ns": "...", "pid": "...", "cmd": "..."}.
    """
    mac = normalize_mac(mac).lower()
    holders: List[Dict[str, str]] = []

    if not (_have("lsns") and _have("nsenter")):
        return holders

    cp = _run(["lsns", "-t", "net", "-o", "NS,PID,COMMAND", "--noheadings"], check=False, sudo=False)
    for line in (cp.stdout or "").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 2)
        if len(parts) < 2:
            continue
        ns_id, pid_s = parts[0], parts[1]
        cmd = parts[2] if len(parts) > 2 else ""
        if not pid_s.isdigit():
            continue

        cp2 = _run(["nsenter", "-t", pid_s, "-n", "ip", "-o", "link"], check=False, sudo=True)
        if mac in (cp2.stdout or "").lower():
            holders.append({"ns": ns_id, "pid": pid_s, "cmd": cmd})
            if len(holders) >= max_hits:
                break

    return holders


def delete_netns(ns: str) -> None:
    # IMPORTANT: kill processes in the netns first; otherwise the netns can stay alive
    # as an unnamed namespace (not shown in `ip netns list`), causing MAC collisions later.
    try:
        kill_netns_pids(ns)
    except Exception:
        pass

    if _netns_exists(ns):
        _run(["ip", "netns", "del", ns], check=True, sudo=True, timeout=10)


def _get_link_json(ns: Optional[str], iface: str) -> Dict[str, Any]:
    if ns:
        cp = _ip_netns_exec(ns, ["ip", "-j", "link", "show", "dev", iface], timeout=10)
    else:
        cp = _run(["ip", "-j", "link", "show", "dev", iface], check=True, sudo=False, timeout=10)
    data = json.loads(cp.stdout or "[]")
    if not data:
        raise CmdError(f"cannot read link json for {iface} (ns={ns})")
    return data[0]


def get_iface_mac(iface: str, ns: Optional[str] = None) -> str:
    j = _get_link_json(ns, iface)
    addr = j.get("address")
    if not addr:
        raise CmdError(f"no mac address found for iface={iface} ns={ns}")
    return normalize_mac(addr)


def get_ipv4_addr(iface: str, ns: Optional[str] = None) -> Optional[str]:
    if ns:
        cp = _ip_netns_exec(ns, ["ip", "-4", "-j", "addr", "show", "dev", iface], timeout=10)
    else:
        cp = _run(["ip", "-4", "-j", "addr", "show", "dev", iface], check=True, sudo=False, timeout=10)
    data = json.loads(cp.stdout or "[]")
    if not data:
        return None
    infos = data[0].get("addr_info", [])
    for it in infos:
        if it.get("family") == "inet" and it.get("local"):
            return it["local"]
    return None


def get_default_route(ns: str) -> Optional[str]:
    cp = _ip_netns_exec(ns, ["ip", "route", "show", "default"], timeout=10)
    out = (cp.stdout or "").strip()
    return out if out else None


# ---------------------------
# DNS / resolv.conf helpers
# ---------------------------

def _read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def _parse_nameservers_from_resolv(text: str) -> List[str]:
    nss = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("nameserver"):
            parts = line.split()
            if len(parts) >= 2:
                nss.append(parts[1].strip())
    return nss


def get_host_nameservers() -> List[str]:
    """
    Return usable host nameservers.
    If /etc/resolv.conf points to 127.0.0.53, try /run/systemd/resolve/resolv.conf.
    """
    etc = _read_text("/etc/resolv.conf")
    nss = _parse_nameservers_from_resolv(etc)

    # systemd-resolved stub detected
    if any(ns.startswith("127.") for ns in nss):
        alt = _read_text("/run/systemd/resolve/resolv.conf")
        alt_nss = _parse_nameservers_from_resolv(alt)
        # pick non-localhost if possible
        alt_nss = [x for x in alt_nss if not x.startswith("127.")]
        if alt_nss:
            return alt_nss

    # filter localhost
    nss2 = [x for x in nss if not x.startswith("127.")]
    return nss2


def _write_text(path: str, content: str) -> None:
    # write as current user; if need root, caller should place in /tmp and chmod.
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def build_resolv_conf(nameservers: List[str]) -> str:
    lines = []
    for ns in nameservers:
        lines.append(f"nameserver {ns}")
    # keep it minimal
    lines.append("options timeout:1 attempts:2")
    return "\n".join(lines) + "\n"


def netns_exec_with_resolv(ns: str, resolv_path: str, cmd: List[str], timeout: Optional[int] = None) -> subprocess.CompletedProcess:
    """
    Run cmd in netns, but with a per-command mount namespace that bind-mounts resolv_path onto /etc/resolv.conf.
    This avoids polluting host resolv.conf and fixes systemd-resolved stub issues in netns.
    Requires: unshare + mount (root/sudo).
    """
    if not _have("unshare"):
        # fallback: run without resolv fix
        return _ip_netns_exec(ns, cmd, timeout=timeout)

    # Build a safe shell command
    # unshare -m sh -c 'mount --bind <resolv_path> /etc/resolv.conf; exec <cmd...>'
    quoted_resolv = shlex.quote(resolv_path)
    quoted_cmd = " ".join(shlex.quote(x) for x in cmd)
    sh_cmd = f"mount --bind {quoted_resolv} /etc/resolv.conf && exec {quoted_cmd}"
    return _ip_netns_exec(ns, ["unshare", "-m", "sh", "-c", sh_cmd], timeout=timeout)


# ---------------------------
# DHCP helpers
# ---------------------------

_DHCLIENT_HAS_TIMEOUT: Optional[bool] = None


def dhclient_has_timeout() -> bool:
    global _DHCLIENT_HAS_TIMEOUT
    if _DHCLIENT_HAS_TIMEOUT is not None:
        return _DHCLIENT_HAS_TIMEOUT
    if not _have("dhclient"):
        _DHCLIENT_HAS_TIMEOUT = False
        return False
    cp = _run(["dhclient", "--help"], check=False, sudo=False)
    help_txt = (cp.stdout or "") + "\n" + (cp.stderr or "")
    _DHCLIENT_HAS_TIMEOUT = ("-timeout" in help_txt)
    return _DHCLIENT_HAS_TIMEOUT


def parse_dhclient_lease_for_dns_and_router(lease_text: str) -> Tuple[List[str], Optional[str]]:
    """
    Parse ISC dhclient lease file text and extract:
      - option domain-name-servers
      - option routers
    Return (dns_list, router)
    """
    dns_list: List[str] = []
    router: Optional[str] = None

    # take last occurrence as "latest"
    dns_matches = re.findall(r"option\s+domain-name-servers\s+([^;]+);", lease_text, flags=re.IGNORECASE)
    if dns_matches:
        last = dns_matches[-1]
        # may be: "192.168.1.1, 8.8.8.8"
        parts = [p.strip() for p in re.split(r"[,\s]+", last) if p.strip()]
        dns_list = parts

    r_matches = re.findall(r"option\s+routers\s+([^;]+);", lease_text, flags=re.IGNORECASE)
    if r_matches:
        last = r_matches[-1].strip()
        # sometimes multiple routers; take first
        router = re.split(r"[,\s]+", last)[0].strip() if last else None

    return dns_list, router

def _extract_last_lease_block(lease_text: str, iface: str, ip4: Optional[str] = None) -> Optional[str]:
    """Return the last 'lease { ... }' block for iface (and optionally matching fixed-address ip4)."""
    if not lease_text:
        return None
    blocks = re.findall(r"lease\s*\{.*?\}\s*", lease_text, flags=re.DOTALL | re.IGNORECASE)
    if not blocks:
        return None
    iface_pat = re.compile(rf"interface\s+\"{re.escape(iface)}\"\s*;", flags=re.IGNORECASE)
    ip_pat = None
    if ip4:
        ip_pat = re.compile(rf"fixed-address\s+{re.escape(ip4)}\s*;", flags=re.IGNORECASE)
    matched: List[str] = []
    for b in blocks:
        if not iface_pat.search(b):
            continue
        if ip_pat and not ip_pat.search(b):
            continue
        matched.append(b)
    return matched[-1] if matched else None



def dhcp_release_renew(ns: str, iface: str, timeout_sec: int = 25, release_then_renew: bool = False) -> Dict[str, Any]:
    """
    Renew DHCP for iface within netns.

    If release_then_renew=True and dhclient is available, performs a two-phase refresh to
    help DHCP servers apply updated reservations immediately:
      1) dhclient -1 (obtain current lease)
      2) dhclient -r (DHCPRELEASE best-effort)
      3) dhclient -1 (obtain a fresh lease)

    Returns dict: {"ipv4": "...", "dns": [...], "router": "...", "lease_file": "..."}

    NOTE:
      Some environments block dhclient from creating arbitrary lease/pid files under /tmp.
      Therefore we run dhclient without -lf/-pf by default and parse the system lease DB
      (typically /var/lib/dhcp/dhclient.leases) for DNS/router options.
    """
    lease_db = os.environ.get("LAN_MACVLAN_DHCLIENT_LEASE_DB", "/var/lib/dhcp/dhclient.leases")

    def _dhclient_one_shot(tsec: int) -> None:
        """Run dhclient one-shot (v4) inside netns."""
        cmd = ["dhclient", "-4", "-v", "-1"]
        if dhclient_has_timeout():
            cmd += ["-timeout", str(tsec)]
            _ip_netns_exec(ns, cmd + [iface], timeout=tsec + 10)
        else:
            _ip_netns_exec(ns, cmd + [iface], timeout=tsec)

    def _dhclient_release() -> bool:
        """Best-effort DHCPRELEASE. Returns True if command succeeded."""
        cmd = ["dhclient", "-4", "-v", "-r", iface]
        try:
            _ip_netns_exec(ns, cmd, timeout=10)
            return True
        except Exception:
            return False

    # best-effort clear old addr
    try:
        _ip_netns_exec(ns, ["ip", "addr", "flush", "dev", iface], timeout=10)
    except CmdError:
        pass

    if _have("dhclient"):
        # Phase 1: obtain current lease
        _dhclient_one_shot(timeout_sec)

        pre_ip4 = get_ipv4_addr(iface, ns=ns)
        if not pre_ip4:
            raise CmdError(f"dhclient completed but no IPv4 on {iface} in netns={ns}")

        release_ok = False
        if release_then_renew:
            # Phase 2: best-effort DHCPRELEASE while the lease is active
            release_ok = _dhclient_release()
            # Clear address before re-request
            try:
                _ip_netns_exec(ns, ["ip", "addr", "flush", "dev", iface], timeout=10)
            except CmdError:
                pass
            # Phase 3: obtain a fresh lease
            _dhclient_one_shot(timeout_sec)

        ip4 = get_ipv4_addr(iface, ns=ns)
        if not ip4:
            raise CmdError(f"dhclient completed but no IPv4 on {iface} in netns={ns}")

        # Parse DHCP options from system lease DB (host FS)
        lease_text = _read_text(lease_db)
        block = _extract_last_lease_block(lease_text, iface, ip4=ip4) or _extract_last_lease_block(lease_text, iface)
        dns_list, router = ([], None)
        if block:
            dns_list, router = parse_dhclient_lease_for_dns_and_router(block)

        info = {
            "ipv4": ip4,
            "dns": dns_list,
            "router": router,
            "lease_file": lease_db,
            "lease_matched": bool(block),
        }
        if release_then_renew:
            info.update({
                "release_then_renew": True,
                "release_ok": bool(release_ok),
                "pre_ipv4": pre_ip4,
            })
        return info


    if _have("udhcpc"):
        # udhcpc doesn't produce ISC lease file; use host resolv or router fallback later
        _ip_netns_exec(
            ns,
            ["udhcpc", "-i", iface, "-n", "-q", "-T", "3", "-t", str(max(1, timeout_sec // 3))],
            timeout=timeout_sec + 5,
        )
        ip4 = get_ipv4_addr(iface, ns=ns)
        if not ip4:
            raise CmdError(f"udhcpc completed but no IPv4 on {iface} in netns={ns}")
        return {"ipv4": ip4, "dns": [], "router": None, "lease_file": None}

    raise CmdError("no DHCP client found: need dhclient or udhcpc on control PC")

def create_macvlan_in_netns(
    parent_iface: str,
    ns: str,
    v_iface: str,
    mac: Optional[str] = None,
    mode: str = "bridge",
) -> str:
    if not _iface_exists(parent_iface):
        raise CmdError(f"parent iface not found: {parent_iface}")

    ensure_netns(ns)
    mac = normalize_mac(mac) if mac else gen_local_admin_mac()

    _run(
        ["ip", "link", "add", "link", parent_iface, "name", v_iface, "address", mac,
         "type", "macvlan", "mode", mode],
        check=True, sudo=True, timeout=10,
    )
    _run(["ip", "link", "set", v_iface, "netns", ns], check=True, sudo=True, timeout=10)
    
    try:
        _ip_netns_exec(ns, ["ip", "link", "set", v_iface, "up"], timeout=10)
    except CmdError as e:
        msg = str(e)
        if "address already in use" in msg.lower():
            holders = []
            try:
                holders = find_mac_holders(mac)
            except Exception:
                holders = []
            extra = ""
            if holders:
                extra_lines = ["Detected existing holders of this MAC (may be in unnamed netns):"]
                for h in holders:
                    extra_lines.append(f"  ns={h.get('ns')} pid={h.get('pid')} cmd={h.get('cmd')}")
                extra = "\n" + "\n".join(extra_lines)
            raise CmdError(msg + extra) from e
        raise

    return get_iface_mac(v_iface, ns=ns)


def delete_iface_in_netns(ns: str, v_iface: str) -> None:
    try:
        _ip_netns_exec(ns, ["ip", "link", "del", v_iface], timeout=10)
    except CmdError:
        pass


# ---------------------------
# Context manager class
# ---------------------------

@dataclass
class MacvlanNS:
    parent_iface: Optional[str] = None
    ns: str = "auto"
    v_iface: str = "lan_test0"
    mac: Optional[str] = None
    mode: str = "bridge"

    _created_ns: Optional[str] = None
    _actual_mac: Optional[str] = None
    _dhcp_info: Dict[str, Any] = None

    def __post_init__(self):
        if self.ns == "auto":
            self.ns = f"dhcpns_{os.getpid()}_{secrets.token_hex(2)}"
        if self.v_iface == "auto":
            # host-side ifname limit is usually 15 chars; keep it short
            self.v_iface = gen_unique_iface(prefix="lan")
        if not self.parent_iface:
            self.parent_iface = detect_parent_iface(["eno2", "ens19"])
        self._dhcp_info = {}

    
    def __enter__(self) -> "MacvlanNS":
        self._created_ns = self.ns
        try:
            self._actual_mac = create_macvlan_in_netns(
                parent_iface=self.parent_iface,
                ns=self.ns,
                v_iface=self.v_iface,
                mac=self.mac,
                mode=self.mode,
            )
            return self
        except Exception:
            # Best-effort cleanup even if creation failed mid-way.
            try:
                delete_iface_in_netns(self.ns, self.v_iface)
            except Exception:
                pass
            try:
                delete_netns(self.ns)
            except Exception:
                pass
            self._created_ns = None
            self._actual_mac = None
            raise

    def __exit__(self, exc_type, exc, tb) -> None:
        self.cleanup()

    @property
    def mac_addr(self) -> str:
        if not self._actual_mac:
            raise CmdError("MacvlanNS not created yet")
        return self._actual_mac

    def renew_dhcp(self, timeout_sec: int = 25, release_then_renew: bool = False) -> Dict[str, Any]:
        info = dhcp_release_renew(self.ns, self.v_iface, timeout_sec=timeout_sec, release_then_renew=release_then_renew)
        self._dhcp_info = info or {}
        return self._dhcp_info

    def get_ipv4(self) -> Optional[str]:
        return get_ipv4_addr(self.v_iface, ns=self.ns)

    def get_dns_servers(self) -> List[str]:
        dns = self._dhcp_info.get("dns") or []
        # if dhclient didn't provide, fallback to host usable nameservers
        if not dns:
            dns = get_host_nameservers()
        # last fallback: try router in default 192.168.1.1 style if present
        router = self._dhcp_info.get("router")
        if not dns and router:
            dns = [router]
        return dns

    def ping(self, host: str = "google.com", count: int = 3, timeout_sec: int = 6) -> None:
        """
        Ping a host from inside netns. If host is a domain, inject per-command resolv.conf built from DHCP DNS
        to avoid systemd-resolved stub issues.
        """
        # if it's clearly an IPv4 literal, no DNS needed
        if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host):
            _ip_netns_exec(self.ns, ["ping", "-c", str(count), "-W", str(timeout_sec), host],
                           timeout=timeout_sec * count + 5)
            return

        dns = self.get_dns_servers()
        # If still empty, we'll attempt without DNS fix (may fail)
        if dns:
            resolv_text = build_resolv_conf(dns)
            resolv_path = f"/tmp/resolv_{self.ns}_{os.getpid()}.conf"
            _write_text(resolv_path, resolv_text)
            # run ping with per-command bind mounted resolv.conf
            netns_exec_with_resolv(
                self.ns,
                resolv_path,
                ["ping", "-c", str(count), "-W", str(timeout_sec), host],
                timeout=timeout_sec * count + 5,
            )
        else:
            _ip_netns_exec(self.ns, ["ping", "-c", str(count), "-W", str(timeout_sec), host],
                           timeout=timeout_sec * count + 5)

    def cleanup(self) -> None:
        if self._created_ns:
            delete_iface_in_netns(self._created_ns, self.v_iface)
            delete_netns(self._created_ns)
        self._created_ns = None
        self._actual_mac = None
        self._dhcp_info = {}


# ---------------------------
# CLI for quick verification
# ---------------------------

def _main():
    import argparse

    ap = argparse.ArgumentParser(description="Create macvlan in netns, renew DHCP, ping, and cleanup safely.")
    ap.add_argument("--parent", default=None, help="parent wired iface (e.g. eno2 / ens19). default: auto-detect")
    ap.add_argument("--ns", default="auto", help="netns name; default auto unique")
    ap.add_argument("--iface", default="lan_test0", help="macvlan iface name inside netns (or 'auto' for a unique name)")
    ap.add_argument("--mac", default=None, help="optional fixed MAC (02:.. recommended)")
    ap.add_argument("--renew", action="store_true", help="run DHCP renew after create")
    ap.add_argument("--release-then-renew", action="store_true", help="with --renew: do dhclient -1, DHCPRELEASE (dhclient -r), then dhclient -1 again to force rebind")
    ap.add_argument("--ping", default=None, help="ping host inside netns after renew (e.g. google.com)")
    ap.add_argument("--json", action="store_true", help="print json result")
    args = ap.parse_args()

    with MacvlanNS(parent_iface=args.parent, ns=args.ns, v_iface=args.iface, mac=args.mac) as mv:
        out: Dict[str, Any] = {
            "ns": mv.ns,
            "iface": mv.v_iface,
            "parent": mv.parent_iface,
            "mac": mv.mac_addr,
            "need_sudo": _need_sudo(),
        }

        if args.renew:
            info = mv.renew_dhcp(release_then_renew=bool(args.release_then_renew))
            out["dhcp"] = info
            out["ipv4"] = mv.get_ipv4()
            out["default_route"] = get_default_route(mv.ns)
            out["dns"] = mv.get_dns_servers()

        if args.ping:
            mv.ping(args.ping)
            out["ping_ok"] = True
            out["ping_target"] = args.ping

        if args.json:
            print(json.dumps(out, indent=2))
        else:
            print(out)


if __name__ == "__main__":
    _main()


