#!/usr/bin/env python3
import os, sys, re, json, subprocess, time, urllib.parse, html as htmllib
import base64

DEFAULT_URL = os.getenv("CPE_WAREHOUSE_URL", "https://192.168.1.1/cgi-bin/warehouse.cgi")

ENV_USER_KEYS = ["WAREHOUSE_ID", "WAREHOUSE_USER", "CPE_WAREHOUSE_ID"]
ENV_PW_KEYS   = ["WAREHOUSE_PASSWORD", "WAREHOUSE_PW", "CPE_WAREHOUSE_PASSWORD"]

def _env_first(keys):
    for k in keys:
        v = os.getenv(k)
        if v:
            return v
    return ""

def print_help():
    print("""cpe_warehouse_info - Fetch Warehouse Info table from warehouse.cgi

Usage:
  cpe_warehouse_info [URL] [FLAGS]...

Flags:
  --user USER, --id USER        Warehouse credentials username
  --password PW, --pw PW        Warehouse credentials password
  --json                        Output JSON
  --compact                     JSON in one line
  --value, -v                   Value only (when one field)
  -f, --field NAME              Select field (repeatable)
  --decode-base64               Also output decoded Default SSID/Password (extra keys)
  --timeout SEC                 curl max-time seconds (default: 3)
  --retries N                   retry times (default: 5)
  --sleep SEC                   sleep between retries (default: 2)
  --ipv 4|6|auto                force curl -4 or -6; default auto
  -h, --help                    Help

Env:
  CPE_WAREHOUSE_URL
  WAREHOUSE_ID / WAREHOUSE_USER / CPE_WAREHOUSE_ID
  WAREHOUSE_PASSWORD / WAREHOUSE_PW / CPE_WAREHOUSE_PASSWORD

Examples:
  cpe_warehouse_info --json
  cpe_warehouse_info -f "IPv4 Address" --value
  cpe_warehouse_info https://myrouter/cgi-bin/warehouse.cgi --json
  cpe_warehouse_info 'https://[fe80::1%25eno2]/cgi-bin/warehouse.cgi' --ipv 6 --json
""")

def _curl(args, timeout=5):
    try:
        return subprocess.check_output(
            args,
            timeout=timeout,
            stderr=subprocess.DEVNULL,
        ).decode("utf-8", "ignore")
    except Exception:
        return ""

def curl_get(url, user, pw, timeout=3, ip_mode="auto"):
    # IPv6 URLs contain brackets [] which curl treats as URL globbing unless --globoff/-g is used.
    # Also, IPv6 link-local redirects often drop the zone (%25<iface>), so avoid -L in that case.
    follow = True
    if ip_mode == "6" and "%25" in url:
        follow = False

    base = ["curl", "--globoff", "-fsSk", "--anyauth", "-u", f"{user}:{pw}", "-m", str(timeout)]
    if follow:
        base.insert(3, "-L")  # after -fsSk

    if ip_mode == "4":
        base.insert(1, "-4")
    elif ip_mode == "6":
        base.insert(1, "-6")
    return _curl(base + [url], timeout=timeout + 1)

def _strip_tags(s):
    s = re.sub(r"(?is)<script[^>]*>.*?</script>", "", s)
    s = re.sub(r"(?is)<style[^>]*>.*?</style>", "", s)
    s = re.sub(r"(?is)<[^>]+>", " ", s)
    s = htmllib.unescape(s)
    s = s.replace("\r", "").replace("&nbsp;", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def parse_warehouse_table(html):
    """
    Parse <table> rows: <tr><td>Field</td><td>Setting</td></tr>
    Return dict: {Field: Setting}
    """
    html = html.replace("\r", "").replace("&nbsp;", " ")
    # 先抓所有 tr，再抽 td 兩欄
    rows = re.findall(r"(?is)<tr[^>]*>(.*?)</tr>", html)
    out = {}
    for r in rows:
        tds = re.findall(r"(?is)<t[dh][^>]*>(.*?)</t[dh]>", r)
        if len(tds) < 2:
            continue
        k = _strip_tags(tds[0])
        v = _strip_tags(tds[1])
        if not k or k.lower() == "field":
            continue
        out[k] = v
    return out

def try_b64decode(s):
    try:
        return base64.b64decode(s).decode("utf-8", "ignore").strip()
    except Exception:
        return ""

def main():
    argv = sys.argv[1:]
    if ("-h" in argv) or ("--help" in argv):
        print_help()
        return

    # URL: first positional not starting with '-'
    url = DEFAULT_URL
    if argv and not argv[0].startswith("-"):
        url = argv[0]
        argv = argv[1:]

    # parse flags (simple)
    def _get_arg(flag_names, default=""):
        for i, a in enumerate(argv):
            if a in flag_names and i + 1 < len(argv):
                return argv[i + 1]
        return default

    user = _get_arg(["--user", "--id"], _env_first(ENV_USER_KEYS))
    pw   = _get_arg(["--password", "--pw"], _env_first(ENV_PW_KEYS))

    want_json = "--json" in argv
    compact = "--compact" in argv
    value_only = ("--value" in argv) or ("-v" in argv)
    decode_b64 = "--decode-base64" in argv

    timeout = int(_get_arg(["--timeout"], "3") or "3")
    retries = int(_get_arg(["--retries"], "5") or "5")
    sleep_s = int(_get_arg(["--sleep"], "2") or "2")

    ip_mode = _get_arg(["--ipv"], "auto").strip().lower()
    if ip_mode not in ("auto", "4", "6"):
        ip_mode = "auto"

    # selected fields
    selected = []
    for i, a in enumerate(argv):
        if a in ("-f", "--field") and i + 1 < len(argv):
            selected.append(argv[i + 1])

    if not user or not pw:
        print("ERROR: missing warehouse credentials (use --user/--password or env vars)", file=sys.stderr)
        sys.exit(2)

    # fetch with retries
    html = ""
    for _ in range(max(1, retries)):
        html = curl_get(url, user, pw, timeout=timeout, ip_mode=ip_mode)
        if html:
            break
        time.sleep(max(0, sleep_s))

    if not html:
        print("ERROR: cannot fetch warehouse.cgi", file=sys.stderr)
        sys.exit(2)

    data = parse_warehouse_table(html)
    if not data:
        print("ERROR: warehouse table parse failed (no rows)", file=sys.stderr)
        sys.exit(3)

    if decode_b64:
        # 加兩個額外欄位，方便 test case 直接比對
        if "Default SSID" in data:
            data["Default SSID (decoded)"] = try_b64decode(data["Default SSID"])
        if "Default Password" in data:
            data["Default Password (decoded)"] = try_b64decode(data["Default Password"])

    # output
    if selected:
        out = {k: data.get(k, "") for k in selected}
        if want_json:
            if compact:
                print(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
            else:
                print(json.dumps(out, ensure_ascii=False, indent=2))
        else:
            if value_only and len(out) == 1:
                print(next(iter(out.values()), ""))
            elif value_only:
                for k in selected:
                    print(out.get(k, ""))
            else:
                for k in selected:
                    print(f"{k}: {out.get(k,'')}")
        return

    if want_json:
        if compact:
            print(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
        else:
            print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        for k, v in data.items():
            print(f"{k}: {v}")

if __name__ == "__main__":
    main()


