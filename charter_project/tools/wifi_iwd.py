#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import ipaddress
import json
import os
import re
import shutil
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

TOOL = "wifi_iwd"
ANSI_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")


def _strip_ansi(s: str) -> str:
    return ANSI_RE.sub("", s or "")


def _run(cmd: List[str], timeout: int = 30) -> Tuple[int, str, str, float]:
    t0 = time.time()
    env = os.environ.copy()
    env.setdefault("LANG", "C")
    env.setdefault("LC_ALL", "C")
    env.setdefault("TERM", "dumb")  # discourage ANSI
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, timeout=timeout)
    return p.returncode, (p.stdout or ""), (p.stderr or ""), time.time() - t0


def _jprint(obj: Dict[str, Any], pretty: bool = True) -> None:
    print(json.dumps(obj, indent=2 if pretty else None, ensure_ascii=False, sort_keys=False))


def _has_bin(name: str) -> bool:
    return shutil.which(name) is not None


def _systemctl(args: List[str], timeout: int = 25) -> Tuple[int, str, str, float]:
    return _run(["systemctl"] + args, timeout=timeout)


def _svc_is_active(name: str) -> Optional[bool]:
    rc, out, _, _ = _systemctl(["is-active", name], timeout=10)
    out = (out or "").strip()
    if rc == 0 and out == "active":
        return True
    if out in ("inactive", "failed", "activating", "deactivating"):
        return False
    return None


def _ip_link_up(iface: str) -> None:
    _run(["ip", "link", "set", iface, "up"], timeout=8)


def _sysctl_write(key: str, value: str) -> Tuple[bool, str]:
    """
    Best-effort write to /proc/sys (no external sysctl dependency).
    Returns (ok, msg). Missing keys are treated as ok with note.
    """
    path = "/proc/sys/" + key.replace(".", "/")
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(value))
        return True, ""
    except FileNotFoundError:
        return True, f"missing {path}"
    except PermissionError:
        return False, f"permission denied writing {path} (need root)"
    except Exception as e:
        return False, f"failed writing {path}: {e}"


def _fix_ipv6_sysctl(iface: str) -> List[str]:
    """
    Apply minimal IPv6 sysctl tweaks that help Wi-Fi clients receive IPv6 RAs.
    Safe defaults:
      - disable_ipv6 = 0
      - autoconf     = 1
      - accept_ra    = 2
    """
    notes: List[str] = []
    keys = [
        (f"net.ipv6.conf.{iface}.disable_ipv6", "0"),
        (f"net.ipv6.conf.{iface}.autoconf", "1"),
        (f"net.ipv6.conf.{iface}.accept_ra", "2"),
    ]
    for k, v in keys:
        ok, msg = _sysctl_write(k, v)
        if ok:
            notes.append(f"ipv6-sysctl: {k}={v}" + (f" ({msg})" if msg else ""))
        else:
            notes.append(f"ipv6-sysctl: {k}={v} FAILED: {msg}")
    return notes



def _ip4_addr(iface: str) -> Optional[str]:
    rc, out, _, _ = _run(["ip", "-4", "-o", "addr", "show", "dev", iface], timeout=6)
    if rc != 0:
        return None
    m = re.search(r"\binet\s+(\d+\.\d+\.\d+\.\d+/\d+)", out)
    return m.group(1) if m else None


def _mac_addr(iface: str) -> str:
    try:
        with open(f"/sys/class/net/{iface}/address", "r", encoding="utf-8") as f:
            return (f.read() or "").strip()
    except Exception:
        return ""



def _eui64_ll_from_mac(mac: str) -> str:
    # Return link-local IPv6 (no /64) computed from MAC using EUI-64.
    m = (mac or "").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{2}(:[0-9a-f]{2}){5}", m):
        return ""
    b = [int(x, 16) for x in m.split(":" )]
    b[0] ^= 0x02  # flip U/L bit
    eui = b[:3] + [0xFF, 0xFE] + b[3:]
    w = [(eui[i] << 8) | eui[i + 1] for i in range(0, 8, 2)]
    return "fe80::%x:%x:%x:%x" % tuple(w)


def _has_link_local_ipv6(iface: str) -> bool:
    rc, out, _, _ = _run(["ip", "-6", "addr", "show", "dev", iface, "scope", "link"], timeout=6)
    if rc != 0:
        return False
    return bool(re.search(r"inet6\s+fe80:", out, flags=re.I))


def _ensure_link_local_ipv6(iface: str) -> tuple[bool, str]:
    # Best-effort: ensure a fe80::/64 exists on iface.
    if _has_link_local_ipv6(iface):
        return True, "already_present"
    mac = _mac_addr(iface)
    ll = _eui64_ll_from_mac(mac)
    if not ll:
        return False, f"bad_mac:{mac}"
    rc, _, err, _ = _run(["ip", "-6", "addr", "add", f"{ll}/64", "dev", iface], timeout=8)
    if rc == 0:
        return True, f"added:{ll}/64"
    if "File exists" in (err or ""):
        return True, f"exists:{ll}/64"
    return False, "ip6_add_failed:" + (err or "").strip()


def _ip6_addr(iface: str) -> Optional[str]:
    rc, out, _, _ = _run(["ip", "-6", "-o", "addr", "show", "dev", iface], timeout=6)
    if rc != 0:
        return None
    # prefer global, else link-local
    addrs = re.findall(r"\binet6\s+([0-9a-fA-F:]+/\d+)", out)
    if not addrs:
        return None
    for a in addrs:
        if not a.lower().startswith("fe80:"):
            return a
    return addrs[0]


def _ip4_routes(iface: str) -> List[str]:
    rc, out, _, _ = _run(["ip", "-4", "route", "show", "dev", iface], timeout=6)
    if rc != 0:
        return []
    return [x.strip() for x in out.splitlines() if x.strip()]


def _ip6_routes(iface: str) -> List[str]:
    rc, out, _, _ = _run(["ip", "-6", "route", "show", "dev", iface], timeout=6)
    if rc != 0:
        return []
    return [x.strip() for x in out.splitlines() if x.strip()]


def _has_default_route(routes: List[str]) -> bool:
    return any(r == "default" or r.startswith("default ") for r in routes)


def _gw_from_routes(routes: List[str]) -> Optional[str]:
    for r in routes:
        # e.g. "default via 192.168.1.1 ..."
        if r.startswith("default "):
            m = re.search(r"\bvia\s+([0-9a-fA-F:.]+)\b", r)
            if m:
                return m.group(1)
    return None


def _dhcp(iface: str, timeout_s: int = 45) -> Tuple[bool, str, str]:
    """
    returns: (ok, client_name, err)
    """
    if _has_bin("udhcpc"):
        rc, out, err, _ = _run(["udhcpc", "-i", iface, "-q", "-n", "-t", "10", "-T", "3"], timeout=timeout_s)
        if rc == 0:
            return True, "udhcpc", ""
        return False, "udhcpc", (_strip_ansi(err).strip() or _strip_ansi(out).strip() or f"udhcpc rc={rc}")
    if _has_bin("dhclient"):
        rc, out, err, _ = _run(["dhclient", "-1", "-v", iface], timeout=timeout_s)
        if rc == 0:
            return True, "dhclient", ""
        return False, "dhclient", (_strip_ansi(err).strip() or _strip_ansi(out).strip() or f"dhclient rc={rc}")
    return False, "none", "no DHCP client found (need udhcpc or dhclient)"


def _dhcp_release(iface: str) -> None:
    if _has_bin("dhclient"):
        _run(["dhclient", "-r", iface], timeout=15)


def _iwctl(args: List[str], timeout: int = 30) -> Tuple[int, str, str, float]:
    return _run(["iwctl"] + args, timeout=timeout)


def _parse_iwctl_station_show(text: str) -> Dict[str, str]:
    d: Dict[str, str] = {}
    for line in _strip_ansi(text).splitlines():
        s = line.rstrip("\n")
        if not s.strip():
            continue
        if "----" in s:
            continue
        if s.strip().startswith(("Station:", "Settable")):
            continue
        cols = re.split(r"\s{2,}", s.strip())
        if len(cols) >= 2:
            key = cols[0].strip()
            val = " ".join(cols[1:]).strip()
            if key and val:
                d[key] = val
    return d


def _parse_iwctl_networks(text: str) -> List[Dict[str, Any]]:
    nets: List[Dict[str, Any]] = []
    in_table = False
    for line in _strip_ansi(text).splitlines():
        s = line.rstrip("\n")
        if "Available networks" in s:
            in_table = True
            continue
        if not in_table:
            continue
        if not s.strip() or "----" in s:
            continue
        if s.strip().startswith("Network name"):
            continue
        cols = re.split(r"\s{2,}", s.strip())
        if len(cols) >= 3:
            ssid = cols[0].strip().lstrip("> ").strip()
            sec = cols[1].strip()
            sig = cols[2].strip()
            if ssid:
                nets.append({"ssid": ssid, "security": sec, "signal": sig})
    return nets


def _parse_iw_scan(text: str) -> List[Dict[str, Any]]:
    """Parse `iw dev <iface> scan` output into BSS entries (best-effort).

    This is used only when scan_detail is enabled and is additive.
    """
    aps: List[Dict[str, Any]] = []
    cur: Dict[str, Any] = {}

    def flush():
        nonlocal cur
        if cur.get("bssid") or cur.get("ssid"):
            aps.append(cur)
        cur = {}

    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue

        if line.startswith("BSS "):
            flush()
            m = re.match(r"^BSS\s+([0-9a-fA-F:]{17})", line)
            if m:
                cur["bssid"] = m.group(1).lower()
            continue

        if line.startswith("freq:"):
            try:
                cur["freq"] = int(re.findall(r"\d+", line)[0])
            except Exception:
                pass
            continue

        if line.startswith("signal:"):
            try:
                cur["signal_dbm"] = float(re.findall(r"-?\d+\.\d+|-?\d+", line)[0])
            except Exception:
                pass
            continue

        if line.startswith("SSID:"):
            cur["ssid"] = line.split(":", 1)[1].strip()
            continue

    flush()
    return aps


def _band_from_freq(freq: int) -> str:
    if 2400 <= freq < 3000:
        return "2g"
    if 4900 <= freq < 5900:
        return "5g"
    if freq >= 5900:
        return "6g"
    return "unknown"


def _iwctl_station_show(iface: str) -> Tuple[bool, Dict[str, str], str]:
    rc, out, err, _ = _iwctl(["station", iface, "show"], timeout=15)
    if rc != 0:
        return False, {}, (_strip_ansi(err).strip() or _strip_ansi(out).strip() or f"iwctl show rc={rc}")
    return True, _parse_iwctl_station_show(out), ""


def _iwctl_device_list() -> List[str]:
    rc, out, _, _ = _iwctl(["device", "list"], timeout=15)
    if rc != 0:
        return []
    names: List[str] = []
    for line in _strip_ansi(out).splitlines():
        s = line.strip()
        if not s or "----" in s:
            continue
        if s.startswith(("Devices", "Name")):
            continue
        cols = re.split(r"\s{2,}", s)
        if cols and cols[0]:
            names.append(cols[0].strip())
    return names


def _wait_device_present(iface: str, timeout_s: int = 12) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if iface in _iwctl_device_list():
            return True
        time.sleep(0.5)
    return False


def _wait_ssid_visible(iface: str, ssid: str, timeout_s: int = 15) -> Tuple[bool, List[Dict[str, Any]], str]:
    _iwctl(["station", iface, "scan"], timeout=min(25, timeout_s))
    deadline = time.time() + timeout_s
    last_err = ""
    last_nets: List[Dict[str, Any]] = []
    while time.time() < deadline:
        rc, out, err, _ = _iwctl(["station", iface, "get-networks"], timeout=15)
        if rc == 0:
            last_nets = _parse_iwctl_networks(out)
            if any(n.get("ssid") == ssid for n in last_nets):
                return True, last_nets, ""
        else:
            last_err = (_strip_ansi(err).strip() or _strip_ansi(out).strip() or f"get-networks rc={rc}")
        time.sleep(1.0)
    if last_err:
        return False, last_nets, last_err
    return False, last_nets, f"ssid '{ssid}' not found in get-networks within {timeout_s}s"


def _iwctl_station_disconnect(iface: str) -> Tuple[bool, str]:
    rc, out, err, _ = _iwctl(["station", iface, "disconnect"], timeout=20)
    if rc == 0:
        return True, ""
    return False, (_strip_ansi(err).strip() or _strip_ansi(out).strip() or f"iwctl disconnect rc={rc}")


def _stop_for_takeover() -> List[str]:
    notes: List[str] = []
    rc, out, err, _ = _systemctl(["stop", "NetworkManager"], timeout=30)
    notes.append("stopped NetworkManager" if rc == 0 else f"stop NetworkManager failed: {(_strip_ansi(err) or _strip_ansi(out)).strip() or rc}")

    rc, out, err, _ = _systemctl(["stop", "wpa_supplicant"], timeout=30)
    notes.append("stopped wpa_supplicant" if rc == 0 else "stop wpa_supplicant skipped/failed")

    rc, out, err, _ = _systemctl(["restart", "iwd"], timeout=30)
    notes.append("restarted iwd" if rc == 0 else f"restart iwd failed: {(_strip_ansi(err) or _strip_ansi(out)).strip() or rc}")
    return notes


def _restore_nm(iface: str, unmanaged: bool) -> Tuple[List[str], bool]:
    """
    returns (notes, unmanaged_applied)
    """
    notes: List[str] = []
    unmanaged_applied = False

    rc, out, err, _ = _systemctl(["start", "NetworkManager"], timeout=30)
    if rc == 0:
        notes.append("started NetworkManager")
    else:
        notes.append(f"start NetworkManager failed: {(_strip_ansi(err) or _strip_ansi(out)).strip() or rc}")
        return notes, unmanaged_applied

    if unmanaged:
        if _has_bin("nmcli"):
            rc, out, err, _ = _run(["nmcli", "dev", "set", iface, "managed", "no"], timeout=15)
            if rc == 0:
                notes.append(f"nmcli set {iface} unmanaged")
                unmanaged_applied = True
            else:
                notes.append(f"nmcli set unmanaged failed: {(_strip_ansi(err) or _strip_ansi(out)).strip() or rc}")
        else:
            notes.append("nmcli not found; cannot set unmanaged (NM may take over Wi-Fi)")
    return notes, unmanaged_applied


def _ip_rule_add(parts: List[str], timeout: int = 8) -> Tuple[bool, str]:
    cmd = ["ip", "rule", "add"] + parts
    rc, out, err, _ = _run(cmd, timeout=timeout)
    if rc == 0:
        return True, ""
    msg = (_strip_ansi(err).strip() or _strip_ansi(out).strip() or f"ip rule add rc={rc}")
    if "File exists" in msg or "RTNETLINK answers: File exists" in msg:
        return True, "exists"
    return False, msg


def _ip_route_replace(parts: List[str], timeout: int = 8) -> Tuple[bool, str]:
    cmd = ["ip", "route", "replace"] + parts
    rc, out, err, _ = _run(cmd, timeout=timeout)
    if rc == 0:
        return True, ""
    return False, (_strip_ansi(err).strip() or _strip_ansi(out).strip() or f"ip route replace rc={rc}")


def _ip_route_show_defaults_dev(iface: str, timeout: int = 8) -> List[str]:
    rc, out, _, _ = _run(["ip", "-4", "route", "show", "default", "dev", iface], timeout=timeout)
    if rc != 0:
        return []
    return [x.strip() for x in out.splitlines() if x.strip()]



def _remove_main_default_routes_for_iface(iface: str) -> int:
    """Remove IPv4 main-table default routes for this iface (any metric/proto variants).

    Prevents stale routes like:
      default dev wlan0 scope link metric 1076 linkdown
    from blackholing traffic later when other default routes change.
    """
    routes = _ip_route_show_defaults_dev(iface)
    if not routes:
        return 0
    removed = 0
    for line in routes:
        s = (line or "").strip()
        if not s:
            continue
        toks = s.split()
        rc, _, _, _ = _run(["ip", "-4", "route", "del"] + toks, timeout=8)
        if rc == 0:
            removed += 1
    return removed

def _ip_route_del_tokens(tokens: List[str], timeout: int = 8) -> Tuple[bool, str]:
    rc, out, err, _ = _run(["ip", "route", "del"] + tokens, timeout=timeout)
    if rc == 0:
        return True, ""
    msg = (_strip_ansi(err).strip() or _strip_ansi(out).strip() or f"ip route del rc={rc}")
    if "No such process" in msg:
        return True, "absent"
    return False, msg


def _purge_main_defaults_for_iface(iface: str) -> Tuple[int, Optional[str]]:
    """
    Remove all IPv4 main-table default routes for this iface (any metric/proto variants).
    Returns (removed_count, error)
    """
    defaults = _ip_route_show_defaults_dev(iface)
    removed = 0
    for line in defaults:
        toks = line.split()
        ok, msg = _ip_route_del_tokens(toks)
        if ok:
            removed += 1
        else:
            return removed, f"failed deleting existing default '{line}': {msg}"
    return removed, None


def _apply_main_route_controls(iface: str, gw4: Optional[str], route_metric: Optional[int], no_main_default: bool) -> Tuple[List[str], Optional[str]]:
    """
    Returns (notes, error)
    - Only modifies main table defaults if user requested route_metric or no_main_default.
    """
    notes: List[str] = []

    # If user didn't request any main-table manipulation, do nothing.
    if not no_main_default and route_metric is None:
        return notes, None

    removed, err = _purge_main_defaults_for_iface(iface)
    if err:
        return notes, err
    if removed:
        notes.append(f"main: removed {removed} existing default route(s) for iface")

    if no_main_default:
        notes.append("main: removed default route for iface")
        return notes, None

    # route_metric requested
    if route_metric is not None:
        if not gw4:
            return notes, "route-metric requested but gw4 not found"
        ok, msg = _ip_route_replace(["default", "via", gw4, "dev", iface, "metric", str(route_metric)])
        if ok:
            notes.append(f"main: set default metric={route_metric} via {gw4}")
            return notes, None
        return notes, f"failed setting route metric: {msg}"

    return notes, None


def _apply_pbr(
    iface: str,
    ip4_cidr: str,
    gw4: str,
    table: int,
    priority: int,
    from_ip: bool,
    fwmark: Optional[str],
) -> Tuple[List[str], Optional[str]]:
    """
    Setup:
      - table route for connected subnet + default via gw
      - ip rules for from-ip and/or fwmark
    """
    notes: List[str] = []

    ip_str, _ = ip4_cidr.split("/", 1)
    ip = ipaddress.ip_interface(ip4_cidr)
    net = str(ip.network)

    ok, msg = _ip_route_replace([net, "dev", iface, "scope", "link", "table", str(table), "src", ip_str])
    if not ok:
        return notes, f"pbr: failed subnet route replace: {msg}"
    notes.append(f"pbr: table {table} subnet {net} dev {iface}")

    ok, msg = _ip_route_replace(["default", "via", gw4, "dev", iface, "table", str(table)])
    if not ok:
        return notes, f"pbr: failed default route replace: {msg}"
    notes.append(f"pbr: table {table} default via {gw4}")

    pr = priority
    if fwmark:
        ok2, msg2 = _ip_rule_add(["priority", str(pr), "fwmark", fwmark, "lookup", str(table)])
        if not ok2:
            return notes, f"pbr: failed add fwmark rule: {msg2}"
        notes.append(f"pbr: rule prio={pr} fwmark {fwmark} -> table {table}")
        pr += 1

    if from_ip:
        ok2, msg2 = _ip_rule_add(["priority", str(pr), "from", f"{ip_str}/32", "lookup", str(table)])
        if not ok2:
            return notes, f"pbr: failed add from-ip rule: {msg2}"
        notes.append(f"pbr: rule prio={pr} from {ip_str}/32 -> table {table}")

    return notes, None


def cmd_status(iface: str) -> Dict[str, Any]:
    ok, st, err = _iwctl_station_show(iface)
    ip4 = _ip4_addr(iface)
    ip6 = _ip6_addr(iface)
    routes4 = _ip4_routes(iface)
    routes6 = _ip6_routes(iface)
    gw4 = _gw_from_routes(routes4)
    gw6 = _gw_from_routes(routes6)

    nm = _svc_is_active("NetworkManager")
    iwd = _svc_is_active("iwd")

    freq = None
    band = None
    if ok and st.get("Frequency"):
        try:
            freq = int(re.findall(r"\d+", st["Frequency"])[0])
            band = _band_from_freq(freq)
        except Exception:
            pass

    return {
        "tool": TOOL,
        "cmd": "status",
        "ok": ok,
        "sec": 0.0,
        "iface": iface,
        "iwd_active": iwd,
        "nm_active": nm,
        "station": st if ok else None,
        "ssid": st.get("Connected network") if ok else None,
        "bssid": st.get("ConnectedBss") if ok else None,
        "freq": freq,
        "band": band,
        "ip4": ip4,
        "gw4": gw4 or "",
        "routes4": routes4,
        "default_route4": _has_default_route(routes4),
        "ip6": ip6,
        "gw6": gw6 or "",
        "routes6": routes6,
        "default_route6": _has_default_route(routes6),
        "error": err or None,
    }


def cmd_scan(iface: str, timeout: int = 25, scan_detail: bool = False) -> Dict[str, Any]:
    """Scan available networks.

    Notes / robustness:
    - On some systems, iwd scan may get stuck ("Operation already in progress") and `get-networks`
      can return stale cache. We treat scan as best-effort and add retries.
    - If scan appears stuck for too long and sudo NOPASSWD is available, we can restart iwd
      (sudo -n systemctl restart iwd) and retry once.

    Backward compatible:
      - keeps existing fields: {count, aps=[{ssid,security,signal}]}
    Additive (when scan_detail=True):
      - adds `aps_detail` from `iw dev <iface> scan` (bssid/freq/signal_dbm/ssid)
    """

    def _systemctl_bin() -> str:
        # Allow override for distros where systemctl is in /usr/bin
        return os.environ.get("SYSTEMCTL_BIN", "systemctl")

    def _restart_iwd_noninteractive() -> Tuple[bool, str]:
        # Requires sudoers NOPASSWD for restarting iwd.
        if not _has_bin("sudo"):
            return False, "sudo not found"
        cmd = ["sudo", "-n", _systemctl_bin(), "restart", "iwd"]
        rc, out, err, _ = _run(cmd, timeout=25)
        if rc == 0:
            return True, "restarted iwd via sudo -n"
        msg = (_strip_ansi(err).strip() or _strip_ansi(out).strip() or f"rc={rc}")
        return False, f"restart iwd failed: {msg}"

    t0 = time.time()
    notes: List[str] = []

    # Best-effort ensure iwd is running. On locked-down systems, this may require auth; do not fail scan.
    try:
        rc0, out0, err0, _ = _systemctl(["start", "iwd"], timeout=20)
        if rc0 != 0:
            notes.append(f"systemctl start iwd failed (ignored): {(_strip_ansi(err0) or _strip_ansi(out0)).strip() or rc0}")
    except Exception as e:
        notes.append(f"systemctl start iwd exception (ignored): {e}")

    _ip_link_up(iface)

    # Optional: richer scan info via `iw` (best-effort). Do not fail scan if this fails.
    aps_detail = None
    aps_detail_err = None
    if scan_detail:
        rc_iw, out_iw, err_iw, _ = _run(["iw", "dev", iface, "scan"], timeout=min(timeout, 60))
        if rc_iw == 0 and out_iw.strip():
            try:
                aps_detail = _parse_iw_scan(out_iw)
            except Exception as e:
                aps_detail = None
                aps_detail_err = f"parse iw scan failed: {e}"
        else:
            aps_detail_err = (_strip_ansi(err_iw).strip() or _strip_ansi(out_iw).strip() or f"iw scan rc={rc_iw}")

    # Trigger an active scan (best-effort). Handle "Operation already in progress" by waiting/retrying.
    scan_stuck = False
    scan_deadline = time.time() + min(max(timeout, 10), 60)
    scan_attempts = 0
    while time.time() < scan_deadline:
        scan_attempts += 1
        rc_s, out_s, err_s, _ = _iwctl(["station", iface, "scan"], timeout=min(timeout, 25))
        msg = (_strip_ansi(err_s).strip() or _strip_ansi(out_s).strip() or "")
        if "Operation already in progress" in msg:
            time.sleep(2.0)
            continue
        # If scan command itself fails for other reasons, stop retrying; we'll still try get-networks.
        if rc_s != 0 and msg:
            notes.append(f"iwctl scan failed (ignored): {msg}")
        break
    else:
        scan_stuck = True
        notes.append(f"scan appears stuck (Operation already in progress) after {scan_attempts} attempts")

    # If scan seems stuck, attempt a one-shot iwd restart (if sudo -n is allowed), then retry scan once.
    if scan_stuck:
        ok_r, msg_r = _restart_iwd_noninteractive()
        notes.append(msg_r)
        if ok_r:
            # retry scan once after restart
            rc_s, out_s, err_s, _ = _iwctl(["station", iface, "scan"], timeout=min(timeout, 25))
            msg = (_strip_ansi(err_s).strip() or _strip_ansi(out_s).strip() or "")
            if rc_s != 0 and msg:
                notes.append(f"iwctl scan after restart failed (ignored): {msg}")
            time.sleep(2.0)

    # Fetch networks; retry a few times to reduce stale-cache flakiness.
    last_err = ""
    out2 = ""
    for _ in range(3):
        rc2, out2, err2, _ = _iwctl(["station", iface, "get-networks"], timeout=min(timeout, 25))
        if rc2 == 0 and (out2 or "").strip():
            break
        last_err = (_strip_ansi(err2).strip() or _strip_ansi(out2).strip() or f"iwctl get-networks rc={rc2}")
        time.sleep(1.0)
    else:
        return {
            "tool": TOOL,
            "cmd": "scan",
            "ok": False,
            "sec": round(time.time() - t0, 3),
            "iface": iface,
            "count": 0,
            "aps": None,
            "aps_detail": aps_detail if scan_detail else None,
            "aps_detail_error": aps_detail_err if scan_detail else None,
            "notes": notes or None,
            "error": last_err or "failed to get networks",
        }

    nets = _parse_iwctl_networks(out2)
    return {
        "tool": TOOL,
        "cmd": "scan",
        "ok": True,
        "sec": round(time.time() - t0, 3),
        "iface": iface,
        "count": len(nets),
        "aps": nets,
        "aps_detail": aps_detail if scan_detail else None,
        "aps_detail_error": aps_detail_err if scan_detail else None,
        "notes": notes or None,
        "error": None,
    }


def cmd_disconnect(iface: str, restore_nm: bool, unmanaged: bool) -> Dict[str, Any]:
    t0 = time.time()
    notes: List[str] = []

    # 1) Ask iwd to disconnect (best-effort).
    ok, err = _iwctl_station_disconnect(iface)
    if not ok:
        e = (err or "").lower()
        if any(k in e for k in ["not connected", "not configured", "no such", "disconnected", "failed to find", "device not found"]):
            notes.append(f"iwctl: {err} (treat as already disconnected)")
            ok, err = True, ""

    # 2) Release DHCP + cleanup stale default route on this Wi-Fi iface (best-effort).
    try:
        _dhcp_release(iface)
    except Exception as e:
        notes.append(f"dhcp: release failed: {e}")

    try:
        removed = _remove_main_default_routes_for_iface(iface)
        if removed:
            notes.append(f"main: removed {removed} default route(s) for iface")
    except Exception as e:
        notes.append(f"main: default cleanup failed: {e}")

    # 3) Restore NetworkManager if requested.
    if restore_nm:
        n, _ = _restore_nm(iface, unmanaged)
        notes += n

    st = cmd_status(iface)

    # If iwctl reported an error but station is clearly down (no SSID, no IP), do not fail disconnect.
    if not ok:
        if not st.get("ssid") and not st.get("ip4"):
            notes.append(f"iwctl: disconnect error ignored (station already down): {err}")
            ok, err = True, ""

    return {
        "tool": TOOL,
        "cmd": "disconnect",
        "ok": ok,
        "sec": round(time.time() - t0, 3),
        "iface": iface,
        "notes": notes or None,
        "error": err or None,
        "status": st,
    }

def cmd_ensure(
    iface: str,
    ssid: str,
    psk: str,
    band: Optional[str],
    fix_ipv6_sysctl: bool,
    timeout: int,
    dhcp_timeout: int,
    takeover: bool,
    restore_nm: bool,
    unmanaged: bool,
    route_metric: Optional[int],
    no_main_default: bool,
    pbr_table: Optional[int],
    pbr_priority: int,
    pbr_from_ip: bool,
    pbr_fwmark: Optional[str],
) -> Dict[str, Any]:
    t0 = time.time()
    stage = "start"
    notes: List[str] = []
    net_notes: List[str] = []

    if not _has_bin("iwctl"):
        return {
            "tool": TOOL,
            "cmd": "ensure",
            "ok": False,
            "stage": "precheck",
            "sec": 0.0,
            "iface": iface,
            "target_ssid": ssid,
            "error": "iwctl not found (install iwd)",
            "status": None,
        }

    _systemctl(["start", "iwd"], timeout=20)

    if takeover:
        stage = "takeover"
        notes += _stop_for_takeover()

    stage = "wait_device"
    # If the requested iface is not present in iwd (common when scripts hardcode wlan0),
    # fall back to an available Wi-Fi device to avoid false negatives.
    devs = _iwctl_device_list()
    if devs and iface not in devs:
        preferred = iface
        # Prefer stable USB dongle names (wlx*) if present
        pick = next((d for d in devs if d.startswith("wlx")), devs[0])
        iface = pick
        notes.append(f"iface {preferred} not present in iwd devices={devs}; fallback to {iface}")

    # If the requested iface is not present in iwd (common when scripts hardcode wlan0),
    # fall back to an available Wi-Fi device to avoid false negatives.
    devs = _iwctl_device_list()
    if devs and iface not in devs:
        preferred = iface
        # Prefer stable USB dongle names (wlx*) if present
        pick = next((d for d in devs if d.startswith("wlx")), devs[0])
        iface = pick
        notes.append(f"iface {preferred} not present in iwd devices={devs}; fallback to {iface}")

    _ip_link_up(iface)
    if not _wait_device_present(iface, timeout_s=12):
        if restore_nm:
            n, _ = _restore_nm(iface, unmanaged)
            notes += n
        return {
            "tool": TOOL,
            "cmd": "ensure",
            "ok": False,
            "stage": stage,
            "sec": round(time.time() - t0, 3),
            "iface": iface,
            "target_ssid": ssid,
            "error": f"device {iface} not present in iwd (iwctl device list)",
            "notes": notes or None,
            "status": cmd_status(iface),
        }

    # Optional: apply IPv6 sysctl tweaks for this Wi-Fi iface (best-effort).
    if fix_ipv6_sysctl:
        try:
            notes += _fix_ipv6_sysctl(iface)
        except Exception as e:
            notes.append(f"ipv6-sysctl: exception: {e}")
    # already connected? then skip connect
    stage = "precheck_connected"
    ok_show, st0, _ = _iwctl_station_show(iface)
    if not (ok_show and st0.get("State", "").lower() == "connected" and st0.get("Connected network") == ssid):
        stage = "scan_wait_ssid"
        seen, _, seen_err = _wait_ssid_visible(iface, ssid, timeout_s=min(20, timeout))
        if not seen:
            notes.append(f"ssid not visible before connect (will try anyway): {seen_err}")

        stage = "connect"
        rc, out, err, _ = _iwctl(["station", iface, "connect", ssid, "--passphrase", psk], timeout=timeout)
        if rc != 0:
            notes.append(f"connect returned rc={rc}: {(_strip_ansi(err) or _strip_ansi(out)).strip()}")

    stage = "wait_connected"
    deadline = time.time() + timeout
    last: Dict[str, str] = {}
    while time.time() < deadline:
        ok_show, st, _ = _iwctl_station_show(iface)
        if ok_show:
            last = st
            if st.get("State", "").lower() == "connected" and st.get("Connected network") == ssid:
                break
        time.sleep(1.0)
    else:
        if restore_nm:
            n, _ = _restore_nm(iface, unmanaged)
            notes += n
        return {
            "tool": TOOL,
            "cmd": "ensure",
            "ok": False,
            "stage": stage,
            "sec": round(time.time() - t0, 3),
            "iface": iface,
            "target_ssid": ssid,
            "error": f"timeout waiting connected (last={last})",
            "notes": notes or None,
            "status": cmd_status(iface),
        }

    stage = "dhcp"
    ok_dhcp, client, err_dhcp = _dhcp(iface, timeout_s=dhcp_timeout)
    if not ok_dhcp:
        if restore_nm:
            n, _ = _restore_nm(iface, unmanaged)
            notes += n
        return {
            "tool": TOOL,
            "cmd": "ensure",
            "ok": False,
            "stage": stage,
            "sec": round(time.time() - t0, 3),
            "iface": iface,
            "target_ssid": ssid,
            "error": f"dhcp failed ({client}): {err_dhcp}",
            "notes": notes or None,
            "status": cmd_status(iface),
        }

    stage = "verify_pre_restore"
    status_before_restore = cmd_status(iface)

    # Ensure this Wi-Fi iface has an IPv4 default route if DHCP didn"t install one.
    # This is required for tests that do: ping -I <iface> <internet_ip>.
    # We keep metric high so it won"t override the primary wired default route.
    try:
        if status_before_restore.get("ip4") and (not status_before_restore.get("default_route4")):
            gw4 = status_before_restore.get("gw4") or _gw_from_routes(status_before_restore.get("routes4", []))
            if not gw4:
                ip = (status_before_restore.get("ip4") or "").split("/", 1)[0]
                parts = ip.split(".")
                if len(parts) == 4:
                    gw4 = ".".join(parts[:3] + ["1"])  # common home/LAB gateway
            metric = route_metric if route_metric is not None else int(os.environ.get("WIFI_ROUTE_METRIC", "5000"))
            if gw4:
                ok_rt, msg_rt = _ip_route_replace(["default", "via", gw4, "dev", iface, "metric", str(metric)])
                if ok_rt:
                    notes.append(f"main: ensured default via {gw4} metric={metric}")
                else:
                    notes.append(f"main: ensure default FAILED: {msg_rt}")
    except Exception as e:
        notes.append(f"main: ensure default exception: {e}")
    if not status_before_restore.get("ip4"):
        if restore_nm:
            n, _ = _restore_nm(iface, unmanaged)
            notes += n
        return {
            "tool": TOOL,
            "cmd": "ensure",
            "ok": False,
            "stage": stage,
            "sec": round(time.time() - t0, 3),
            "iface": iface,
            "target_ssid": ssid,
            "error": "no IPv4 after DHCP (pre-restore)",
            "notes": notes or None,
            "status_before_restore": status_before_restore,
            "status": cmd_status(iface),
        }

    if band:
        want = {"2.4g": "2g", "24g": "2g", "2g": "2g", "5g": "5g", "6g": "6g"}.get(band.strip().lower(), band.strip().lower())
        got = status_before_restore.get("band")
        if got and want in ("2g", "5g", "6g") and got != want:
            if restore_nm:
                n, _ = _restore_nm(iface, unmanaged)
                notes += n
            return {
                "tool": TOOL,
                "cmd": "ensure",
                "ok": False,
                "stage": "band_check",
                "sec": round(time.time() - t0, 3),
                "iface": iface,
                "target_ssid": ssid,
                "error": f"connected band mismatch: want {want} got {got}",
                "notes": notes or None,
                "status_before_restore": status_before_restore,
                "status": cmd_status(iface),
            }

    unmanaged_applied = False
    if restore_nm:
        stage = "restore_nm"
        n, unmanaged_applied = _restore_nm(iface, unmanaged)
        notes += n

    stage = "verify_post_restore"
    status_after_restore = cmd_status(iface)

    # lla_fix_post_restore: NetworkManager restore/unmanaged may drop fe80:: on Wi-Fi iface
    if restore_nm and unmanaged_applied and not status_after_restore.get("ip6"):
        ok_ll, msg_ll = _ensure_link_local_ipv6(iface)
        net_notes.append(f"main: ensure ll6 post-restore: {ok_ll} ({msg_ll})")
        status_after_restore = cmd_status(iface)

    # If NM unmanaged toggling flushed IP, re-run DHCP
    if restore_nm and unmanaged_applied and not status_after_restore.get("ip4"):
        stage = "dhcp_after_restore"
        ok2, client2, err2 = _dhcp(iface, timeout_s=dhcp_timeout)
        if not ok2:
            return {
                "tool": TOOL,
                "cmd": "ensure",
                "ok": False,
                "stage": stage,
                "sec": round(time.time() - t0, 3),
                "iface": iface,
                "target_ssid": ssid,
                "error": f"dhcp after restore failed ({client2}): {err2}",
                "notes": notes or None,
                "status_before_restore": status_before_restore,
                "status": cmd_status(iface),
            }
        status_after_restore = cmd_status(iface)

    if not status_after_restore.get("ip4"):
        return {
            "tool": TOOL,
            "cmd": "ensure",
            "ok": False,
            "stage": "final_verify",
            "sec": round(time.time() - t0, 3),
            "iface": iface,
            "target_ssid": ssid,
            "error": "no IPv4 at end",
            "notes": notes or None,
            "status_before_restore": status_before_restore,
            "status": status_after_restore,
        }

    # ===== Net controls / PBR (apply at the end) =====

    # ensure default route (post-restore) if missing
    try:
        if status_after_restore.get("ip4"):
            r4 = status_after_restore.get("routes4", []) or []
            if not _has_default_route(r4):
                gw4_guess = status_after_restore.get("gw4") or _gw_from_routes(r4)
                if not gw4_guess:
                    ip = (status_after_restore.get("ip4") or "").split("/", 1)[0]
                    parts = ip.split(".")
                    if len(parts) == 4:
                        gw4_guess = ".".join(parts[:3] + ["1"])
                metric = route_metric if route_metric is not None else int(os.environ.get("WIFI_ROUTE_METRIC", "5000"))
                if gw4_guess:
                    ok_rt, msg_rt = _ip_route_replace(["default", "via", gw4_guess, "dev", iface, "metric", str(metric)])
                    if ok_rt:
                        net_notes.append(f"main: ensured default via {gw4_guess} metric={metric} (post-restore)")
                        status_after_restore = cmd_status(iface)
                    else:
                        net_notes.append(f"main: ensure default FAILED (post-restore): {msg_rt}")
    except Exception as e:
        net_notes.append(f"main: ensure default exception (post-restore): {e}")

    stage = "net_controls"
    ip4_cidr = status_after_restore["ip4"]
    routes4 = status_after_restore.get("routes4", [])
    gw4 = status_after_restore.get("gw4") or _gw_from_routes(routes4)

    # (2) main route control
    n2, err2 = _apply_main_route_controls(iface, gw4 if gw4 else None, route_metric, no_main_default)
    net_notes += n2
    if err2:
        return {
            "tool": TOOL,
            "cmd": "ensure",
            "ok": False,
            "stage": stage,
            "sec": round(time.time() - t0, 3),
            "iface": iface,
            "target_ssid": ssid,
            "error": err2,
            "notes": notes or None,
            "net_notes": net_notes or None,
            "status_before_restore": status_before_restore,
            "status": cmd_status(iface),
        }

    # (3) PBR
    if pbr_table is not None:
        if not gw4:
            return {
                "tool": TOOL,
                "cmd": "ensure",
                "ok": False,
                "stage": "pbr",
                "sec": round(time.time() - t0, 3),
                "iface": iface,
                "target_ssid": ssid,
                "error": "pbr requested but gw4 not found (no default route via on iface at time of setup)",
                "notes": notes or None,
                "net_notes": net_notes or None,
                "status_before_restore": status_before_restore,
                "status": cmd_status(iface),
            }

        n3, err3 = _apply_pbr(
            iface=iface,
            ip4_cidr=ip4_cidr,
            gw4=gw4,
            table=pbr_table,
            priority=pbr_priority,
            from_ip=pbr_from_ip,
            fwmark=pbr_fwmark,
        )
        net_notes += n3
        if err3:
            return {
                "tool": TOOL,
                "cmd": "ensure",
                "ok": False,
                "stage": "pbr",
                "sec": round(time.time() - t0, 3),
                "iface": iface,
                "target_ssid": ssid,
                "error": err3,
                "notes": notes or None,
                "net_notes": net_notes or None,
                "status_before_restore": status_before_restore,
                "status": cmd_status(iface),
            }

    final_status = cmd_status(iface)

    return {
        "tool": TOOL,
        "cmd": "ensure",
        "ok": True,
        "stage": "done",
        "sec": round(time.time() - t0, 3),
        "iface": iface,
        "target_ssid": ssid,
        "notes": notes or None,
        "net_notes": net_notes or None,
        "status_before_restore": status_before_restore,
        "status": final_status,
    }


def _needs_root(cmd: str) -> bool:
    # ensure/disconnect almost always need CAP_NET_ADMIN (DHCP/ip route/ip rule/systemctl)
    return cmd in ("ensure", "disconnect")


def _maybe_reexec_sudo(args: argparse.Namespace) -> None:
    """
    If root is needed but not root, re-exec via: sudo -n <python> <script> <args...>
    """
    if os.geteuid() == 0:
        return
    if not _needs_root(args.cmd):
        return

    if os.environ.get("WIFI_IWD_SUDO_REEXEC") == "1":
        obj = {
            "tool": TOOL,
            "cmd": args.cmd,
            "ok": False,
            "stage": "sudo",
            "error": "needs root but sudo re-exec failed (already attempted)",
        }
        if getattr(args, "json", False):
            _jprint(obj, True)
        else:
            print(obj["error"])
        raise SystemExit(1)

    if not _has_bin("sudo"):
        obj = {
            "tool": TOOL,
            "cmd": args.cmd,
            "ok": False,
            "stage": "sudo",
            "error": "needs root but sudo not found; run as root or install sudo",
        }
        if getattr(args, "json", False):
            _jprint(obj, True)
        else:
            print(obj["error"])
        raise SystemExit(1)

    rc, out, err, _ = _run(["sudo", "-n", "true"], timeout=5)
    if rc != 0:
        msg = (_strip_ansi(err).strip() or _strip_ansi(out).strip() or "sudo -n true failed (password required?)")
        obj = {
            "tool": TOOL,
            "cmd": args.cmd,
            "ok": False,
            "stage": "sudo",
            "error": f"needs root; sudo -n not permitted: {msg}",
        }
        if getattr(args, "json", False):
            _jprint(obj, True)
        else:
            print(obj["error"])
        raise SystemExit(1)

    env = os.environ.copy()
    env["WIFI_IWD_SUDO_REEXEC"] = "1"
    # use the current python interpreter to run this script with same args
    os.execvpe("sudo", ["sudo", "-n", sys.executable] + sys.argv, env)


def main() -> int:
    ap = argparse.ArgumentParser(description="Wi-Fi control via iwd/iwctl + DHCP (+ optional NM restore + optional PBR)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("cmd", choices=["status", "scan", "ensure", "disconnect"])
    ap.add_argument("--iface", required=True)

    ap.add_argument("--ssid")
    ap.add_argument("--band")
    ap.add_argument("--timeout", type=int, default=40)
    ap.add_argument("--dhcp-timeout", type=int, default=45)

    ap.add_argument("--password")
    ap.add_argument("--password-env")

    ap.add_argument("--takeover", action="store_true", help="Stop NetworkManager/wpa_supplicant and restart iwd to avoid races")
    ap.add_argument("--restore-nm", action="store_true", help="Start NetworkManager after ensure/disconnect (keep wired managed by NM)")
    ap.add_argument("--unmanaged", action="store_true", help="When restoring NM, try to set Wi-Fi iface unmanaged (requires nmcli)")
    ap.add_argument("--fix-ipv6-sysctl", action="store_true", help="Apply safe IPv6 sysctl tweaks on this iface (accept_ra=2, autoconf=1, disable_ipv6=0)")

    # (2) main routing control
    ap.add_argument("--route-metric", type=int, default=None, help="Set main table default route metric for this iface (will remove existing iface defaults first).")
    ap.add_argument("--no-main-default", action="store_true", help="Remove main table default route(s) for this iface (for policy routing use-cases)")

    # (3) PBR
    ap.add_argument("--pbr-table", type=int, default=None, help="If set, create routes in this table and add ip rule(s) based on flags below.")
    ap.add_argument("--pbr-priority", type=int, default=10000, help="ip rule priority for PBR rules (fwmark uses this, from-ip uses +1 if both)")
    ap.add_argument("--pbr-from-ip", action="store_true", help="Add rule: from <iface_ipv4>/32 lookup <pbr-table>")
    ap.add_argument("--pbr-fwmark", default=None, help="Add rule: fwmark <mark> lookup <pbr-table> (accepts e.g. 1, 0x1, 0x1/0x1)")

    args = ap.parse_args()

    # Auto sudo re-exec only when needed
    _maybe_reexec_sudo(args)

    if args.cmd == "status":
        obj = cmd_status(args.iface)
        _jprint(obj, True) if args.json else print(obj)
        return 0 if obj.get("ok") else 1

    if args.cmd == "scan":
        scan_detail = (os.environ.get("WIFI_IWD_SCAN_DETAIL", "0").strip() in ("1", "true", "yes", "on"))
        obj = cmd_scan(args.iface, timeout=min(args.timeout, 60), scan_detail=scan_detail)
        _jprint(obj, True) if args.json else print(obj)
        return 0 if obj.get("ok") else 1

    if args.cmd == "disconnect":
        obj = cmd_disconnect(args.iface, restore_nm=args.restore_nm, unmanaged=args.unmanaged)
        _jprint(obj, True) if args.json else print(obj)
        return 0 if obj.get("ok") else 1

    # ensure
    if not args.ssid:
        obj = {"tool": TOOL, "cmd": "ensure", "ok": False, "error": "missing --ssid"}
        _jprint(obj, True) if args.json else print(obj)
        return 2

    psk = args.password
    if psk is None and args.password_env:
        psk = os.environ.get(args.password_env)
    if not psk:
        obj = {"tool": TOOL, "cmd": "ensure", "ok": False, "error": "missing password (--password or --password-env)"}
        _jprint(obj, True) if args.json else print(obj)
        return 2

    obj = cmd_ensure(
        iface=args.iface,
        ssid=args.ssid,
        psk=psk,
        band=args.band,
        fix_ipv6_sysctl=args.fix_ipv6_sysctl,
        timeout=args.timeout,
        dhcp_timeout=args.dhcp_timeout,
        takeover=args.takeover,
        restore_nm=args.restore_nm,
        unmanaged=args.unmanaged,
        route_metric=args.route_metric,
        no_main_default=args.no_main_default,
        pbr_table=args.pbr_table,
        pbr_priority=args.pbr_priority,
        pbr_from_ip=args.pbr_from_ip,
        pbr_fwmark=args.pbr_fwmark,
    )

    _jprint(obj, True) if args.json else print(obj)
    return 0 if obj.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())

