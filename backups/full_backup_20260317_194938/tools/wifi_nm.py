#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
wifi_nm.py - Wi-Fi client control via nmcli (robust across nmcli versions)

Fixes included:
- Works when nmcli DOES NOT support --separator (your environment)
- Correctly parses nmcli -t output with escaped ':' (e.g. BSSID like 90\:D3\:...)
- Parses "5220 MHz" freq format correctly (extracts numeric MHz)
- status() reads IP4.ADDRESS[1] / IP6.ADDRESS[1] variants
"""

import argparse
import json
import os
import re
import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple

TOOL = "wifi_nm"


# ---------------------------
# helpers
# ---------------------------

def _run(cmd: List[str], timeout: int = 30) -> Tuple[int, str, str, float]:
    t0 = time.time()
    env = os.environ.copy()
    env.setdefault("LANG", "C")
    env.setdefault("LC_ALL", "C")
    p = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        timeout=timeout,
    )
    sec = time.time() - t0
    return p.returncode, p.stdout or "", p.stderr or "", sec


def _json_out(obj: Dict[str, Any], pretty: bool = True) -> None:
    print(json.dumps(obj, indent=2 if pretty else None, ensure_ascii=False, sort_keys=False))

def _systemctl(args: List[str], timeout: int = 20) -> Tuple[int, str, str, float]:
    return _run(["systemctl"] + args, timeout=timeout)


def _nm_active() -> Optional[bool]:
    """
    Returns True/False if systemd is available, else None.
    """
    rc, out, err, _ = _systemctl(["is-active", "NetworkManager"], timeout=10)
    txt = (out or err or "").strip()
    if rc == 0 and txt == "active":
        return True
    if txt in ("inactive", "failed", "activating", "deactivating"):
        return False
    return None


def _maybe_start_nm(auto_start_nm: bool) -> Tuple[bool, str]:
    """
    If auto_start_nm is True and NetworkManager is not active, try to start it.
    Returns (ok, msg). If NM status is unknown (no systemd), returns ok=True with note.
    """
    if not auto_start_nm:
        return True, ""
    st = _nm_active()
    if st is True:
        return True, ""
    if st is None:
        return True, "nm status unknown (no systemd?)"
    rc, out, err, _ = _systemctl(["start", "NetworkManager"], timeout=25)
    if rc == 0:
        return True, "started NetworkManager"
    return False, (err.strip() or out.strip() or f"failed to start NetworkManager rc={rc}")




def _remove_main_default_routes_for_iface(iface: str) -> int:
    """Remove IPv4 main-table default routes for this iface (any metric/proto variants).

    This prevents stale routes like:
      default dev wlan0 scope link metric 1076 linkdown
    from blackholing traffic later when other default routes are modified.
    """
    rc, out, _, _ = _run(["ip", "-4", "route", "show", "default", "dev", iface], timeout=8)
    if rc != 0:
        return 0
    removed = 0
    for line in (out or "").splitlines():
        s = line.strip()
        if not s:
            continue
        toks = s.split()
        rc2, _, _, _ = _run(["ip", "-4", "route", "del"] + toks, timeout=8)
        if rc2 == 0:
            removed += 1
    return removed


def _to_int_first_number(s: str) -> int:
    m = re.search(r"\d+", s or "")
    return int(m.group(0)) if m else -1


def _band_from_freq(freq_mhz: int) -> str:
    if 2400 <= freq_mhz < 3000:
        return "2g"
    if 4900 <= freq_mhz < 5900:
        return "5g"
    if freq_mhz >= 5900:
        return "6g"
    return "unknown"


def _norm_band(band: Optional[str]) -> Optional[str]:
    if not band:
        return None
    b = band.strip().lower()
    return {
        "2g": "2g", "2.4g": "2g", "24g": "2g", "2.4": "2g",
        "5g": "5g", "5": "5g",
        "6g": "6g", "6": "6g",
        "any": None, "auto": None, "": None,
    }.get(b, b if b in ("2g", "5g", "6g") else b)


def _is_connected_state(nm_state: str) -> bool:
    return "connected" in (nm_state or "").lower()


def split_nmcli_terse(line: str, sep: str = ":", esc: str = "\\") -> List[str]:
    """
    Split nmcli -t output line by separator, respecting escape (\\: means literal ':').

    Example input:
      SpectrumSetup-6A4D:90\\:D3\\:CF\\:EB\\:6A\\:4B:5220 MHz:100:WPA2

    Should split into 5 fields:
      [SSID, BSSID, FREQ, SIGNAL, SECURITY]
    with unescaped values:
      BSSID becomes 90:D3:CF:EB:6A:4B
    """
    out: List[str] = []
    buf: List[str] = []
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == esc:
            # Escape next char (if any) and include it literally
            if i + 1 < len(line):
                buf.append(line[i + 1])
                i += 2
                continue
            # trailing backslash, keep it
            buf.append(ch)
            i += 1
            continue
        if ch == sep:
            out.append("".join(buf))
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    out.append("".join(buf))
    return out


# ---------------------------
# nmcli feature detection
# ---------------------------

def nmcli_supports_separator() -> bool:
    rc, out, err, _ = _run(["nmcli", "-h"], timeout=10)
    txt = (out or "") + (err or "")
    return "--separator" in txt


# ---------------------------
# status
# ---------------------------

def _parse_nmcli_keyval(text: str) -> Dict[str, str]:
    d: Dict[str, str] = {}
    for line in (text or "").splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        d[k.strip()] = v.strip()
    return d


def status(iface: str) -> Dict[str, Any]:
    rc, out, err, sec = _run(
        [
            "nmcli", "-t",
            "-f",
            "GENERAL.STATE,GENERAL.CONNECTION,GENERAL.HWADDR,"
            "IP4.ADDRESS,IP4.GATEWAY,IP6.ADDRESS,IP6.GATEWAY",
            "dev", "show", iface,
        ],
        timeout=15,
    )
    info = _parse_nmcli_keyval(out)

    nm_state = info.get("GENERAL.STATE", "unknown")
    connection = info.get("GENERAL.CONNECTION")
    hwaddr = info.get("GENERAL.HWADDR")

    ip4 = next((v for k, v in info.items() if k.startswith("IP4.ADDRESS") and v), None)
    gw4 = info.get("IP4.GATEWAY", "")

    ip6 = next((v for k, v in info.items() if k.startswith("IP6.ADDRESS") and v), None)
    gw6 = info.get("IP6.GATEWAY", "")

    return {
        "tool": TOOL,
        "cmd": "status",
        "ok": (rc == 0) or ("not connected" in (err or "").lower()) or ("not active" in (err or "").lower()),
        "sec": round(sec, 3),
        "iface": iface,
        "nm_state": nm_state,
        "connection": connection,
        "hwaddr": hwaddr,
        "ip4": ip4,
        "gw4": gw4,
        "ip6": ip6,
        "gw6": gw6,
        "stderr": err.strip() if err else None,
    }


# ---------------------------
# scan
# ---------------------------

def scan_wifi(iface: str, rescan: bool = True, timeout: int = 25, auto_start_nm: bool = False) -> Tuple[bool, List[Dict[str, Any]], str, float]:
    ok_nm, msg_nm = _maybe_start_nm(auto_start_nm)
    if not ok_nm:
        return False, [], f"NetworkManager not running and auto-start failed: {msg_nm}", 0.0

    cmd = ["nmcli", "-t"]
    sep = "|"
    has_sep = nmcli_supports_separator()
    if has_sep:
        cmd += ["--separator", sep]
    cmd += ["-f", "SSID,BSSID,FREQ,SIGNAL,SECURITY", "dev", "wifi", "list", "ifname", iface]
    if rescan:
        cmd += ["--rescan", "yes"]

    rc, out, err, sec = _run(cmd, timeout=timeout)
    if rc != 0:
        return False, [], (err.strip() or out.strip() or f"nmcli rc={rc}"), sec

    aps: List[Dict[str, Any]] = []
    for line in (out or "").splitlines():
        line = line.strip()
        if not line:
            continue

        if has_sep:
            parts = line.split(sep)
        else:
            # IMPORTANT: parse escaped ':' properly
            parts = split_nmcli_terse(line, sep=":", esc="\\")

        if len(parts) != 5:
            # ignore malformed lines
            continue

        ssid, bssid, freq_s, sig_s, secu = parts
        ssid = (ssid or "").strip()
        if not ssid:
            # skip hidden/blank SSID
            continue

        freq = _to_int_first_number(freq_s)
        signal = _to_int_first_number(sig_s)
        band = _band_from_freq(freq) if freq > 0 else "unknown"

        aps.append({
            "ssid": ssid,
            "bssid": (bssid or "").strip() or None,
            "freq": freq,
            "signal": signal,
            "security": (secu or "").strip(),
            "band": band,
        })

    return True, aps, "", sec


def _pick_best_ap(aps: List[Dict[str, Any]], ssid: str, band: Optional[str]) -> Optional[Dict[str, Any]]:
    band = _norm_band(band)
    cand = [a for a in aps if a.get("ssid") == ssid]
    if not cand:
        return None

    if band in ("2g", "5g", "6g"):
        cand_band = [a for a in cand if a.get("band") == band]
        if cand_band:
            cand = cand_band

    cand.sort(key=lambda a: (a.get("signal", -1) if isinstance(a.get("signal"), int) else -1), reverse=True)
    return cand[0] if cand else None


def active_ap(iface: str) -> Dict[str, Any]:
    cmd = ["nmcli", "-t"]
    sep = "|"
    has_sep = nmcli_supports_separator()
    if has_sep:
        cmd += ["--separator", sep]
    cmd += ["-f", "ACTIVE,SSID,BSSID,FREQ,SIGNAL", "dev", "wifi", "list", "ifname", iface]

    rc, out, err, sec = _run(cmd, timeout=15)
    if rc != 0:
        return {"ok": False, "sec": round(sec, 3), "error": (err.strip() or out.strip() or f"nmcli rc={rc}")}

    best = None
    for line in (out or "").splitlines():
        line = line.strip()
        if not line:
            continue

        if has_sep:
            parts = line.split(sep)
        else:
            parts = split_nmcli_terse(line, sep=":", esc="\\")

        if len(parts) != 5:
            continue

        active, ssid, bssid, freq_s, sig_s = parts
        active = (active or "").strip().lower()
        is_active = active in ("yes", "true", "*")
        if not is_active:
            continue

        freq = _to_int_first_number(freq_s)
        signal = _to_int_first_number(sig_s)
        best = {
            "ssid": (ssid or "").strip() or None,
            "bssid": (bssid or "").strip() or None,
            "freq": freq,
            "signal": signal,
            "band": _band_from_freq(freq) if freq > 0 else "unknown",
        }
        break

    return {"ok": True, "sec": round(sec, 3), "active": best}


# ---------------------------
# connect / ensure
# ---------------------------

def disconnect(iface: str) -> Dict[str, Any]:
    rc, out, err, sec = _run(["nmcli", "dev", "disconnect", iface], timeout=20)

    notes: List[str] = []
    removed = _remove_main_default_routes_for_iface(iface)
    if removed:
        notes.append(f"main: removed {removed} default route(s) for iface")

    return {
        "tool": TOOL,
        "cmd": "disconnect",
        "ok": (rc == 0) or ("not connected" in (err or "").lower()) or ("not active" in (err or "").lower()),
        "sec": round(sec, 3),
        "iface": iface,
        "notes": notes or None,
        "stderr": err.strip() if err else None,
        "stdout": out.strip() if out else None,
        "current": status(iface),
    }


def ensure_wifi(
    iface: str,
    ssid: str,
    password: Optional[str],
    password_env: Optional[str],
    band: Optional[str],
    bssid: Optional[str],
    timeout: int,
    retries: int,
    rescan: bool,
    auto_start_nm: bool,
) -> Dict[str, Any]:

    t0 = time.time()

    result: Dict[str, Any] = {
        "tool": TOOL,
        "cmd": "ensure",
        "ok": False,
        "stage": None,
        "sec": None,
        "iface": iface,
        "target_ssid": ssid,
        "target_bssid": bssid,
        "error": None,
        "current": status(iface),
    }

    psk = password
    if psk is None and password_env:
        psk = os.environ.get(password_env)

    if psk is None:
        result["stage"] = "input"
        result["error"] = "missing password (use --password or --password-env)"
        result["sec"] = round(time.time() - t0, 3)
        return result

    want_band = _norm_band(band)

    for attempt in range(1, max(1, retries) + 1):
        cur = status(iface)
        result["current"] = cur

        if cur.get("ok") and _is_connected_state(cur.get("nm_state", "")) and cur.get("connection") == ssid:
            if want_band in ("2g", "5g", "6g"):
                ap = active_ap(iface)
                act = ap.get("active")
                if act and act.get("band") == want_band:
                    result["ok"] = True
                    result["stage"] = "verify"
                    result["sec"] = round(time.time() - t0, 3)
                    return result
                if act and act.get("band") not in (want_band, "unknown"):
                    result["stage"] = "verify_band"
                    result["error"] = f"connected but band mismatch: want {want_band}, got {act.get('band')}"
                else:
                    result["ok"] = True
                    result["stage"] = "verify"
                    result["sec"] = round(time.time() - t0, 3)
                    return result
            else:
                result["ok"] = True
                result["stage"] = "verify"
                result["sec"] = round(time.time() - t0, 3)
                return result

        result["stage"] = "scan"
        ok, aps, scan_err, _scan_sec = scan_wifi(iface, rescan=rescan, timeout=min(25, timeout), auto_start_nm=auto_start_nm)
        if not ok:
            result["error"] = f"scan failed: {scan_err}"
            if attempt < retries:
                time.sleep(2)
                continue
            result["sec"] = round(time.time() - t0, 3)
            result["current"] = status(iface)
            return result

        if not any(a.get("ssid") == ssid for a in aps):
            result["stage"] = "pick_ap"
            result["error"] = f"ssid_not_found_or_signal_too_low: {ssid}"
            if attempt < retries:
                time.sleep(2)
                continue
            result["sec"] = round(time.time() - t0, 3)
            result["current"] = status(iface)
            return result

        chosen_bssid = bssid
        if not chosen_bssid:
            best = _pick_best_ap(aps, ssid, want_band)
            if best and best.get("bssid"):
                chosen_bssid = best["bssid"]

        result["target_bssid"] = chosen_bssid

        _run(["nmcli", "dev", "disconnect", iface], timeout=15)

        result["stage"] = "connect"
        cmd = ["nmcli", "dev", "wifi", "connect", ssid, "password", psk, "ifname", iface]
        if chosen_bssid:
            cmd += ["bssid", chosen_bssid]

        rc, out, err, _conn_sec = _run(cmd, timeout=timeout)
        if rc != 0:
            result["error"] = (err.strip() or out.strip() or f"connect failed rc={rc}")
            if attempt < retries:
                time.sleep(3)
                continue
            result["sec"] = round(time.time() - t0, 3)
            result["current"] = status(iface)
            return result

        result["stage"] = "verify"
        deadline = time.time() + timeout
        while time.time() < deadline:
            cur = status(iface)
            result["current"] = cur
            if cur.get("ok") and _is_connected_state(cur.get("nm_state", "")) and cur.get("connection") == ssid:
                if want_band in ("2g", "5g", "6g"):
                    ap = active_ap(iface)
                    act = ap.get("active")
                    if act and act.get("band") not in (want_band, "unknown"):
                        result["stage"] = "verify_band"
                        result["error"] = f"band mismatch after connect: want {want_band}, got {act.get('band')}"
                        break
                result["ok"] = True
                result["sec"] = round(time.time() - t0, 3)
                return result
            time.sleep(1.5)

        if attempt < retries:
            time.sleep(2)
            continue

        result["sec"] = round(time.time() - t0, 3)
        result["current"] = status(iface)
        if not result.get("error"):
            result["error"] = "timeout waiting for connected state"
        return result

    result["sec"] = round(time.time() - t0, 3)
    result["current"] = status(iface)
    if not result.get("error"):
        result["error"] = "failed"
    return result


# ---------------------------
# CLI
# ---------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Wi-Fi control via nmcli (compatible without --separator)")
    ap.add_argument("--json", action="store_true", help="output JSON")
    ap.add_argument("--pretty", action="store_true", help="pretty JSON (default when --json)")

    ap.add_argument("--iface", help="Wi-Fi interface (e.g., wlx...)")
    ap.add_argument("--ssid", help="target SSID")
    ap.add_argument("--bssid", help="target BSSID (optional)")
    ap.add_argument("--band", help="preferred/required band: 2g/5g/6g (optional)")
    ap.add_argument("--password", help="Wi-Fi password (PSK)")
    ap.add_argument("--password-env", help="read PSK from environment variable name")
    ap.add_argument("--timeout", type=int, default=35, help="timeout seconds")
    ap.add_argument("--retries", type=int, default=3, help="retries")
    ap.add_argument("--no-rescan", action="store_true", help="do not force rescan")
    ap.add_argument("--auto-start-nm", action="store_true", help="try to start NetworkManager via systemctl if it is not running")
    ap.add_argument("cmd", choices=["status", "scan", "ensure", "disconnect", "active"], help="command")

    args = ap.parse_args()
    pretty = True if (args.json or args.pretty) else False
    rescan = not args.no_rescan

    if args.cmd in ("status", "scan", "disconnect", "active") and not args.iface:
        obj = {"tool": TOOL, "cmd": args.cmd, "ok": False, "error": "missing --iface"}
        _json_out(obj, pretty=True) if args.json else print(obj)
        return 2

    if args.cmd == "status":
        obj = status(args.iface)
        _json_out(obj, pretty=True) if args.json else print(obj)
        return 0 if obj.get("ok") else 1

    if args.cmd == "active":
        obj = {"tool": TOOL, "cmd": "active", "iface": args.iface}
        apinfo = active_ap(args.iface)
        obj.update(apinfo)
        _json_out(obj, pretty=True) if args.json else print(obj)
        return 0 if obj.get("ok") else 1

    if args.cmd == "scan":
        ok, aps, err, sec = scan_wifi(args.iface, rescan=rescan, timeout=min(25, args.timeout), auto_start_nm=args.auto_start_nm)
        obj = {
            "tool": TOOL,
            "cmd": "scan",
            "ok": ok,
            "sec": round(sec, 3),
            "iface": args.iface,
            "count": len(aps) if ok else 0,
            "aps": aps if ok else None,
            "error": err if not ok else None,
        }
        _json_out(obj, pretty=True) if args.json else print(obj)
        return 0 if ok else 1

    if args.cmd == "disconnect":
        obj = disconnect(args.iface)
        _json_out(obj, pretty=True) if args.json else print(obj)
        return 0 if obj.get("ok") else 1

    # ensure
    if not args.iface or not args.ssid:
        obj = {"tool": TOOL, "cmd": "ensure", "ok": False, "error": "missing --iface or --ssid"}
        _json_out(obj, pretty=True) if args.json else print(obj)
        return 2

    obj = ensure_wifi(
        iface=args.iface,
        ssid=args.ssid,
        password=args.password,
        password_env=args.password_env,
        band=args.band,
        bssid=args.bssid,
        timeout=args.timeout,
        retries=args.retries,
        rescan=rescan,
        auto_start_nm=args.auto_start_nm,
    )
    _json_out(obj, pretty=True) if args.json else print(obj)
    return 0 if obj.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
