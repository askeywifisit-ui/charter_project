#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
verify_dhcp_resv_api.py (v3)

Verifier for NOC DHCP Reservation APIs:
  - LIST:   GET    /Customers/{cid}/locations/{loc}/networkConfiguration/dhcpReservations
  - SET:    PUT    /Customers/{cid}/locations/{loc}/networkConfiguration/dhcpReservations/{mac}   (form: ip, hostName)
  - GET:    GET    /Customers/{cid}/locations/{loc}/networkConfiguration/dhcpReservations/{mac}
  - DELETE: DELETE /Customers/{cid}/locations/{loc}/networkConfiguration/dhcpReservations/{mac}

Important observed backend behavior (your real run):
  - After DELETE, GET may return HTTP 200 with an empty JSON object {} (instead of 404).
  - LIST correctly returns [] when deleted.

So this verifier treats BOTH as "not found":
  - HTTP 404
  - HTTP 200 with {} (empty dict)

It also polls after DELETE (eventual consistency).

Env vars (optional):
  NOC_BASE, NOC_CUSTOMER_ID, NOC_TOKEN, NOC_EMAIL, NOC_PASSWORD
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from getpass import getpass
from typing import Any, Dict, Optional, Tuple
from urllib.parse import quote

import requests


def eprint(*a: Any) -> None:
    print(*a, file=sys.stderr)


def api(base: str, path: str) -> str:
    base = base.rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    return f"{base}/api{path}"


def norm_mac(mac: str) -> str:
    m = (mac or "").strip().lower()
    m = m.replace("-", ":")
    if ":" not in m and len(m) == 12:
        m = ":".join(m[i:i + 2] for i in range(0, 12, 2))
    parts = m.split(":")
    if len(parts) != 6 or any(len(p) != 2 for p in parts):
        raise ValueError(f"invalid mac: {mac}")
    int("".join(parts), 16)
    return m


def mac_path(mac: str) -> str:
    return quote(norm_mac(mac), safe="")


def req(
    method: str,
    url: str,
    *,
    token: str = "",
    bearer: bool = False,
    insecure: bool = False,
    timeout: int = 20,
    headers: Optional[Dict[str, str]] = None,
    **kwargs: Any,
) -> requests.Response:
    h = dict(headers or {})
    if token and "Authorization" not in h:
        h["Authorization"] = f"Bearer {token}" if bearer else token
    return requests.request(method, url, headers=h, timeout=timeout, verify=not insecure, **kwargs)


def req_retry_412(
    method: str,
    url: str,
    *,
    token: str,
    bearer: bool,
    insecure: bool,
    retries_412: int,
    wait_sec: float,
    timeout: int,
    **kwargs: Any,
) -> requests.Response:
    last = None
    for i in range(retries_412 + 1):
        r = req(method, url, token=token, bearer=bearer, insecure=insecure, timeout=timeout, **kwargs)
        if r.status_code != 412:
            return r
        last = r
        if i < retries_412:
            time.sleep(wait_sec)
    return last if last is not None else req(method, url, token=token, bearer=bearer, insecure=insecure, timeout=timeout, **kwargs)


def login(base: str, email: str, password: str, *, insecure: bool, bearer: bool, timeout: int) -> str:
    url = api(base, "/Customers/login")
    r = req(
        "POST",
        url,
        insecure=insecure,
        bearer=bearer,
        timeout=timeout,
        headers={"Content-Type": "application/json"},
        json={"email": email, "password": password},
    )
    if r.status_code >= 400:
        raise requests.HTTPError(f"login failed HTTP {r.status_code}: {r.text}", response=r)
    j = r.json()
    tok = j.get("id")
    if not tok:
        raise RuntimeError("login ok but token(id) missing in response")
    return tok


def resolve_location_id(base: str, cid: str, node_id: str, *, token: str, insecure: bool, bearer: bool, timeout: int) -> str:
    url = api(base, f"/Customers/{cid}/nodes/{node_id}")
    r = req("GET", url, token=token, bearer=bearer, insecure=insecure, timeout=timeout)
    if r.status_code >= 400:
        raise requests.HTTPError(f"resolve location failed HTTP {r.status_code}: {r.text}", response=r)
    j = r.json()
    loc = j.get("locationId")
    if not loc:
        raise RuntimeError("locationId missing in node object")
    return loc


def dhcp_list(base: str, cid: str, loc: str, *, token: str, insecure: bool, bearer: bool,
              retries_412: int, wait_sec: float, timeout: int) -> Any:
    url = api(base, f"/Customers/{cid}/locations/{loc}/networkConfiguration/dhcpReservations")
    r = req_retry_412("GET", url, token=token, bearer=bearer, insecure=insecure,
                      retries_412=retries_412, wait_sec=wait_sec, timeout=timeout)
    if r.status_code >= 400:
        raise requests.HTTPError(f"list failed HTTP {r.status_code}: {r.text}", response=r)
    return r.json()


def _is_soft_not_found(status_code: int, body: Any) -> bool:
    # Real backend behavior: 200 + {} means "not found"
    return status_code == 200 and isinstance(body, dict) and len(body) == 0


def dhcp_get(base: str, cid: str, loc: str, mac: str, *, token: str, insecure: bool, bearer: bool,
             retries_412: int, wait_sec: float, timeout: int) -> Tuple[int, Any]:
    url = api(base, f"/Customers/{cid}/locations/{loc}/networkConfiguration/dhcpReservations/{mac_path(mac)}")
    r = req_retry_412("GET", url, token=token, bearer=bearer, insecure=insecure,
                      retries_412=retries_412, wait_sec=wait_sec, timeout=timeout)
    if r.status_code == 404:
        return 404, None
    if r.status_code >= 400:
        raise requests.HTTPError(f"get failed HTTP {r.status_code}: {r.text}", response=r)
    body = r.json()
    if _is_soft_not_found(r.status_code, body):
        return 404, None
    return 200, body


def dhcp_set(base: str, cid: str, loc: str, mac: str, ip: str, hostname: Optional[str], *,
             token: str, insecure: bool, bearer: bool, retries_412: int, wait_sec: float, timeout: int) -> Any:
    url = api(base, f"/Customers/{cid}/locations/{loc}/networkConfiguration/dhcpReservations/{mac_path(mac)}")
    data = {"ip": ip}
    if hostname:
        data["hostName"] = hostname
    r = req_retry_412(
        "PUT",
        url,
        token=token,
        bearer=bearer,
        insecure=insecure,
        retries_412=retries_412,
        wait_sec=wait_sec,
        timeout=timeout,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=data,
    )
    if r.status_code >= 400:
        raise requests.HTTPError(f"set failed HTTP {r.status_code}: {r.text}", response=r)
    return r.json() if r.text.strip() else {"ok": True}


def dhcp_del(base: str, cid: str, loc: str, mac: str, *, token: str, insecure: bool, bearer: bool,
             retries_412: int, wait_sec: float, timeout: int) -> Any:
    url = api(base, f"/Customers/{cid}/locations/{loc}/networkConfiguration/dhcpReservations/{mac_path(mac)}")
    r = req_retry_412("DELETE", url, token=token, bearer=bearer, insecure=insecure,
                      retries_412=retries_412, wait_sec=wait_sec, timeout=timeout)
    if r.status_code >= 400:
        raise requests.HTTPError(f"delete failed HTTP {r.status_code}: {r.text}", response=r)
    return r.json() if r.text.strip() else {"ok": True}


def find_resv_in_list(lst: Any, mac: str) -> Optional[Dict[str, Any]]:
    if not isinstance(lst, list):
        return None
    m = norm_mac(mac)
    for it in lst:
        if isinstance(it, dict):
            it_mac = it.get("mac") or it.get("Mac")
            if it_mac:
                try:
                    if norm_mac(str(it_mac)) == m:
                        return it
                except Exception:
                    continue
    return None


class CmdError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Verify NOC DHCP Reservation APIs (list/get/set/del)")
    ap.add_argument("--base", default=os.environ.get("NOC_BASE", "https://piranha-int.tau.dev-charter.net"))
    ap.add_argument("--customer-id", default=os.environ.get("NOC_CUSTOMER_ID", ""))
    ap.add_argument("--token", default=os.environ.get("NOC_TOKEN", ""))
    ap.add_argument("--email", default=os.environ.get("NOC_EMAIL", ""))
    ap.add_argument("--password", default=os.environ.get("NOC_PASSWORD", ""))
    ap.add_argument("--bearer", action="store_true", help="Use Authorization: Bearer <token>")
    ap.add_argument("--insecure", action="store_true", help="Skip TLS verification")
    ap.add_argument("--timeout", type=int, default=20)

    ap.add_argument("--location-id", default="", help="Location ID (if omitted, resolve from --node-id)")
    ap.add_argument("--node-id", default="", help="Node ID (used to resolve locationId)")

    ap.add_argument("--mac", required=True, help="Target MAC for reservation test")
    ap.add_argument("--ip", required=True, help="Reserved IPv4 to set for the MAC")
    ap.add_argument("--hostname", default="", help="Optional hostName")

    ap.add_argument("--retry-412", type=int, default=0, help="Retry count when HTTP 412 occurs")
    ap.add_argument("--retry-wait", type=float, default=10.0, help="Seconds between 412 retries")

    ap.add_argument("--del-wait-timeout", type=float, default=60.0,
                    help="Seconds to wait after DELETE for GET->404 (or 200+{}) and LIST to remove MAC")
    ap.add_argument("--del-wait-interval", type=float, default=3.0,
                    help="Polling interval seconds while waiting for DELETE propagation")

    ap.add_argument("--restore", action="store_true",
                    help="If a reservation already existed for this MAC, restore it at the end.")
    ap.add_argument("--json", action="store_true", help="Print JSON report")
    return ap.parse_args()


def wait_until_deleted(
    base: str,
    cid: str,
    loc: str,
    mac: str,
    *,
    token: str,
    insecure: bool,
    bearer: bool,
    retries_412: int,
    wait_412_sec: float,
    timeout: int,
    total_timeout: float,
    interval: float,
) -> Tuple[bool, Dict[str, Any]]:
    t0 = time.time()
    detail: Dict[str, Any] = {"waited_sec": 0, "get_status": None, "list_has_mac": None}
    while True:
        code, _ = dhcp_get(base, cid, loc, mac, token=token, insecure=insecure, bearer=bearer,
                          retries_412=retries_412, wait_sec=wait_412_sec, timeout=timeout)
        if code == 404:
            lst = dhcp_list(base, cid, loc, token=token, insecure=insecure, bearer=bearer,
                            retries_412=retries_412, wait_sec=wait_412_sec, timeout=timeout)
            has = find_resv_in_list(lst, mac) is not None
            detail.update({"get_status": 404, "list_has_mac": has, "waited_sec": round(time.time() - t0, 3)})
            return (not has), detail

        detail.update({"get_status": code, "waited_sec": round(time.time() - t0, 3)})
        if time.time() - t0 >= total_timeout:
            try:
                lst = dhcp_list(base, cid, loc, token=token, insecure=insecure, bearer=bearer,
                                retries_412=retries_412, wait_sec=wait_412_sec, timeout=timeout)
                detail["list_has_mac"] = find_resv_in_list(lst, mac) is not None
            except Exception as e:
                detail["list_error"] = str(e)
            return False, detail

        time.sleep(max(0.5, interval))


def main() -> int:
    args = parse_args()
    if not args.customer_id:
        eprint("ERROR: --customer-id (or env NOC_CUSTOMER_ID) is required")
        return 11

    try:
        test_mac = norm_mac(args.mac)
    except Exception as e:
        eprint(f"ERROR: invalid --mac: {e}")
        return 11

    # token acquisition
    tok = args.token
    if not tok:
        if not args.email:
            eprint("ERROR: need --token or --email (and --password or prompt)")
            return 11
        pwd = args.password or getpass("NOC password: ")
        try:
            tok = login(args.base, args.email, pwd, insecure=args.insecure, bearer=args.bearer, timeout=args.timeout)
        except Exception as e:
            eprint(f"ERROR: login failed: {e}")
            return 10

    # resolve location
    loc = args.location_id
    if not loc:
        if not args.node_id:
            eprint("ERROR: need --location-id or --node-id to resolve locationId")
            return 11
        try:
            loc = resolve_location_id(
                args.base, args.customer_id, args.node_id,
                token=tok, insecure=args.insecure, bearer=args.bearer, timeout=args.timeout
            )
        except Exception as e:
            eprint(f"ERROR: resolve locationId failed: {e}")
            return 10

    report: Dict[str, Any] = {
        "base": args.base,
        "customer_id": args.customer_id,
        "location_id": loc,
        "mac": test_mac,
        "ip_set": args.ip,
        "hostname_set": args.hostname or None,
        "steps": [],
        "restored": False,
        "pass": False,
        "notes": [
            "Backend may return 200 + {} for missing reservation; treated as NOT FOUND."
        ],
    }

    existed_before = None
    try:
        lst0 = dhcp_list(
            args.base, args.customer_id, loc,
            token=tok, insecure=args.insecure, bearer=args.bearer,
            retries_412=args.retry_412, wait_sec=args.retry_wait, timeout=args.timeout
        )
        existed_before = find_resv_in_list(lst0, test_mac)
        report["steps"].append({
            "step": "list_before",
            "ok": True,
            "count": len(lst0) if isinstance(lst0, list) else None,
            "existing_for_mac": existed_before
        })
    except Exception as e:
        report["steps"].append({"step": "list_before", "ok": False, "error": str(e)})
        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        return 10

    # SET
    try:
        set_resp = dhcp_set(
            args.base, args.customer_id, loc, test_mac, args.ip, args.hostname or None,
            token=tok, insecure=args.insecure, bearer=args.bearer,
            retries_412=args.retry_412, wait_sec=args.retry_wait, timeout=args.timeout
        )
        report["steps"].append({"step": "set", "ok": True, "response_type": type(set_resp).__name__, "response": set_resp})
    except Exception as e:
        report["steps"].append({"step": "set", "ok": False, "error": str(e)})
        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        return 10

    # GET verify
    try:
        code, got = dhcp_get(
            args.base, args.customer_id, loc, test_mac,
            token=tok, insecure=args.insecure, bearer=args.bearer,
            retries_412=args.retry_412, wait_sec=args.retry_wait, timeout=args.timeout
        )
        if code != 200 or not isinstance(got, dict):
            raise CmdError(f"expected 200 with dict body, got {code} {got}")
        got_ip = got.get("ip") or got.get("Ip")
        got_mac = got.get("mac") or got.get("Mac")
        ok = (got_ip == args.ip and (norm_mac(str(got_mac)) == test_mac if got_mac else True))
        report["steps"].append({"step": "get_after_set", "ok": ok, "got": got, "expect_ip": args.ip})
        if not ok:
            raise CmdError("GET verification failed (ip/mac mismatch)")
    except Exception as e:
        report["steps"].append({"step": "get_after_set", "ok": False, "error": str(e)})
        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        return 2

    # LIST verify contains
    try:
        lst1 = dhcp_list(
            args.base, args.customer_id, loc,
            token=tok, insecure=args.insecure, bearer=args.bearer,
            retries_412=args.retry_412, wait_sec=args.retry_wait, timeout=args.timeout
        )
        entry = find_resv_in_list(lst1, test_mac)
        ok = bool(entry) and (entry.get("ip") == args.ip)
        report["steps"].append({"step": "list_after_set", "ok": ok, "entry": entry})
        if not ok:
            raise CmdError("LIST verification failed (missing or ip mismatch)")
    except Exception as e:
        report["steps"].append({"step": "list_after_set", "ok": False, "error": str(e)})
        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        return 2

    # DEL
    try:
        del_resp = dhcp_del(
            args.base, args.customer_id, loc, test_mac,
            token=tok, insecure=args.insecure, bearer=args.bearer,
            retries_412=args.retry_412, wait_sec=args.retry_wait, timeout=args.timeout
        )
        del_has = find_resv_in_list(del_resp, test_mac) is not None if isinstance(del_resp, list) else None
        report["steps"].append({
            "step": "del",
            "ok": True,
            "response_type": type(del_resp).__name__,
            "del_response_contains_mac": del_has,
            "response": del_resp,
        })
        if del_has is True:
            raise CmdError("DELETE response still contains the MAC; deletion may not have been applied")
    except Exception as e:
        report["steps"].append({"step": "del", "ok": False, "error": str(e)})
        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        return 10

    ok_del, detail = wait_until_deleted(
        args.base, args.customer_id, loc, test_mac,
        token=tok, insecure=args.insecure, bearer=args.bearer,
        retries_412=args.retry_412, wait_412_sec=args.retry_wait, timeout=args.timeout,
        total_timeout=args.del_wait_timeout, interval=args.del_wait_interval
    )
    report["steps"].append({"step": "delete_propagation", "ok": ok_del, **detail})
    if not ok_del:
        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        return 2

    # Optional restore pre-existing reservation
    if args.restore and existed_before:
        try:
            prev_ip = existed_before.get("ip") or existed_before.get("Ip")
            prev_host = existed_before.get("hostname") or existed_before.get("hostName") or existed_before.get("HostName")
            if not prev_ip:
                raise CmdError("existing reservation had no ip; cannot restore safely")
            dhcp_set(
                args.base, args.customer_id, loc, test_mac, str(prev_ip), str(prev_host) if prev_host else None,
                token=tok, insecure=args.insecure, bearer=args.bearer,
                retries_412=args.retry_412, wait_sec=args.retry_wait, timeout=args.timeout
            )
            code3, got3 = dhcp_get(
                args.base, args.customer_id, loc, test_mac,
                token=tok, insecure=args.insecure, bearer=args.bearer,
                retries_412=args.retry_412, wait_sec=args.retry_wait, timeout=args.timeout
            )
            ok = (code3 == 200 and isinstance(got3, dict) and (got3.get("ip") == str(prev_ip)))
            report["steps"].append({"step": "restore_previous", "ok": ok, "previous": existed_before, "got": got3})
            report["restored"] = bool(ok)
        except Exception as e:
            report["steps"].append({"step": "restore_previous", "ok": False, "error": str(e), "previous": existed_before})
            report["restored"] = False

    report["pass"] = True
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("PASS: DHCP reservation API list/get/set/del verified.")
        print(f"location={loc} mac={test_mac} set_ip={args.ip}")
        if args.restore and existed_before:
            print(f"restore={'ok' if report.get('restored') else 'failed'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
