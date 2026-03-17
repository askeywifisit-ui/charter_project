#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple UPnP IGD tester (SSDP + Discovery + basic IGD tests)

功能：
1. 從指定介面 (例如 eno2) 取 IPv4
2. SSDP M-SEARCH 掃描，找出 IGD (InternetGatewayDevice)
3. 抓 rootDesc.xml，解析出 WANIPConnection / WANPPPConnection service
4. 測試：
   - GetExternalIPAddress
   - AddPortMapping -> GetSpecificPortMappingEntry -> DeletePortMapping

特別處理：
- 某些 CPE 的 GetSpecificPortMappingEntry SOAP XML 會壞掉（缺結尾 tag），
  導致 XML parser 失敗。這裡對該 action 加一個「字串式 fallback parser」。
"""

import argparse
import os
import socket
import struct
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
import json
from typing import Optional, Dict, List, Tuple, Any

try:
    import fcntl  # Linux only
except ImportError:  # pragma: no cover
    fcntl = None

# SSDP multicast
MCAST_GRP = "239.255.255.250"
MCAST_PORT = 1900

# 預設介面，可用環境變數 UPNP_IFACE 覆蓋
DEFAULT_IFACE = os.environ.get("UPNP_IFACE", "eno2")


class TestError(Exception):
    """測試失敗用例外。"""
    pass


def log(msg: str) -> None:
    ts = time.strftime("%H:%M:%S")
    print(f"[upnp_tester-CPE 時間 {ts}] {msg}")

# 全域 debug 旗標
DEBUG = False


def debug(msg: str) -> None:
    """
    只有在 DEBUG=True 時才會輸出，用來印 debug 訊息。
    """
    if DEBUG:
        log(msg)


def _classify_phase(msg: str) -> str:
    """
    根據錯誤訊息字串，判斷出是在哪一個測試階段掛掉：

    回傳值：
      - "ssdp"              : SSDP 掃描 / 挑裝置階段
      - "get_external_ip"   : GetExternalIPAddress 相關錯誤
      - "port_add"          : AddPortMapping 新增失敗
      - "port_query"        : GetSpecificPortMappingEntry 查詢失敗 / 空結果
      - "port_query_verify" : 查詢得到結果，但 mapping 資訊不一致（驗證失敗）
      - "port_delete"       : DeletePortMapping 刪除失敗
      - "other"             : 其他有分類，但無法從字串判斷階段
      - "unexpected"        : 非 TestError 的例外（在外層處理）
    """
    if not msg:
        return "other"

    upper = msg.upper()

    if "SSDP" in upper:
        return "ssdp"

    if "GETEXTERNALIPADDRESS" in upper or "EXTERNALIPADDRESS" in upper:
        return "get_external_ip"

    if "ADDPORTMAPPING" in upper:
        return "port_add"

    if "MAPPING MISMATCH" in upper:
        return "port_query_verify"

    if "GETSPECIFICPORTMAPPINGENTRY" in upper:
        return "port_query"

    if "DELETEPORTMAPPING" in upper:
        return "port_delete"

    return "other"


def get_ipv4_for_interface(ifname: str) -> str:
    """取得指定 Linux 介面的 IPv4 位址。"""
    if fcntl is None:
        raise RuntimeError("fcntl 不可用，此函式只支援 Linux。")

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        ifname_bytes = ifname[:15].encode("utf-8")
        # SIOCGIFADDR = 0x8915
        res = fcntl.ioctl(
            s.fileno(),
            0x8915,
            struct.pack("256s", ifname_bytes + b"\0" * (256 - len(ifname_bytes))),
        )
        ip_bytes = res[20:24]
        return socket.inet_ntoa(ip_bytes)
    finally:
        s.close()


def parse_ssdp_response(raw: str) -> Dict[str, str]:
    """解析 SSDP 回應 header。"""
    lines = raw.split("\r\n")
    headers: Dict[str, str] = {}
    for line in lines[1:]:
        if not line or ":" not in line:
            continue
        k, v = line.split(":", 1)
        headers[k.strip().lower()] = v.strip()
    return headers


def ssdp_discover(
    local_ip: str, timeout: float = 3.0, st: str = "ssdp:all"
) -> List[Tuple[Tuple[str, int], Dict[str, str], str]]:
    """從指定來源 IP 發 SSDP M-SEARCH。"""
    log(f"Starting SSDP discovery from {local_ip}, ST={st}, timeout={timeout}s")

    msg = "\r\n".join(
        [
            "M-SEARCH * HTTP/1.1",
            f"HOST: {MCAST_GRP}:{MCAST_PORT}",
            'MAN: "ssdp:discover"',
            f"MX: {int(timeout)}",
            f"ST: {st}",
            "",
            "",
        ]
    ).encode("utf-8")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((local_ip, 0))

        mreq = struct.pack(
            "4s4s", socket.inet_aton(MCAST_GRP), socket.inet_aton(local_ip)
        )
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        sock.settimeout(timeout)
        sock.sendto(msg, (MCAST_GRP, MCAST_PORT))

        results: List[Tuple[Tuple[str, int], Dict[str, str], str]] = []
        while True:
            try:
                data, addr = sock.recvfrom(65535)
            except socket.timeout:
                break
            raw = data.decode(errors="ignore")
            headers = parse_ssdp_response(raw)
            results.append((addr, headers, raw))
        return results
    finally:
        sock.close()


def http_get(url: str, timeout: float = 5.0) -> bytes:
    """簡單 HTTP GET。"""
    log(f"HTTP GET {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "upnp-igd-tester/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def strip_ns(tag: str) -> str:
    """移除 XML namespace。"""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def find_igd_device(location_url: str):
    """
    從 rootDesc.xml 找出 IGD 的 WANIPConnection/WANPPPConnection service。
    回傳 (service_type, control_url_abs, event_sub_url_abs, scpd_url_abs, base_url)
    """
    xml_bytes = http_get(location_url)
    root = ET.fromstring(xml_bytes)

    url_base: Optional[str] = None
    for child in root:
        if strip_ns(child.tag).lower() == "urlbase":
            if child.text and child.text.strip():
                url_base = child.text.strip()
                break

    device = None
    for child in root.iter():
        if strip_ns(child.tag).lower() == "device":
            device = child
            break
    if device is None:
        raise TestError("在 device description 裡找不到 <device>。")

    igd_service = None
    for service in device.iter():
        if strip_ns(service.tag).lower() != "service":
            continue
        stype = control_url = event_sub_url = scpd_url = None
        for elem in service:
            tag = strip_ns(elem.tag).lower()
            if tag == "servicetype":
                stype = (elem.text or "").strip()
            elif tag == "controlurl":
                control_url = (elem.text or "").strip()
            elif tag == "eventsuburl":
                event_sub_url = (elem.text or "").strip()
            elif tag == "scpdurl":
                scpd_url = (elem.text or "").strip()
        if not stype:
            continue
        if "WANIPConnection" in stype or "WANPPPConnection" in stype:
            igd_service = (stype, control_url, event_sub_url, scpd_url)
            break

    if igd_service is None:
        raise TestError("找不到 WANIPConnection / WANPPPConnection 服務。")

    stype, control_url, event_sub_url, scpd_url = igd_service

    if not url_base:
        parsed = urllib.parse.urlparse(location_url)
        base = f"{parsed.scheme}://{parsed.hostname}"
        if parsed.port:
            base += f":{parsed.port}"
        url_base = base.rstrip("/")

    def make_abs(path: Optional[str]) -> Optional[str]:
        if not path:
            return None
        return urllib.parse.urljoin(url_base + "/", path)

    control_abs = make_abs(control_url)
    event_abs = make_abs(event_sub_url)
    scpd_abs = make_abs(scpd_url)

    log(f"Found IGD service: {stype}")
    log(f"  controlURL = {control_abs}")
    log(f"  eventSubURL = {event_abs}")
    log(f"  SCPDURL    = {scpd_abs}")
    return stype, control_abs, event_abs, scpd_abs, url_base


def fallback_parse_getspecific(body: bytes) -> Dict[str, str]:
    """
    給 GetSpecificPortMappingEntry 用的 fallback parser：
    - 不用 XML，直接字串找 <NewXXX>value</NewXXX>
    - 把不可列印字元（例如 0x7f）清掉
    """
    text = body.decode("utf-8", errors="ignore")
    tags = [
        "NewInternalPort",
        "NewInternalClient",
        "NewEnabled",
        "NewPortMappingDescription",
        "NewLeaseDuration",
    ]
    result: Dict[str, str] = {}

    for tag in tags:
        start_tag = f"<{tag}>"
        end_tag = f"</{tag}>"
        start = text.find(start_tag)
        if start == -1:
            continue
        start += len(start_tag)
        end = text.find(end_tag, start)
        if end == -1:
            continue

        raw_val = text[start:end]

        # 只保留「可列印」字元，再 strip 空白
        clean_val = "".join(ch for ch in raw_val if ch.isprintable()).strip()

        result[tag] = clean_val

    return result


def soap_action(
    control_url: str,
    service_type: str,
    action: str,
    arguments: Optional[Dict[str, object]] = None,
    timeout: float = 5.0,
) -> Dict[str, str]:
    """
    對 IGD controlURL 送 SOAP Action，回傳輸出參數 dict。
    特別針對 GetSpecificPortMappingEntry 做 fallback 解析。
    """
    if arguments is None:
        arguments = {}

    body_xml = "".join(f"<{k}>{v}</{k}>" for k, v in arguments.items())

    envelope = f"""<?xml version="1.0"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"
            s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:{action} xmlns:u="{service_type}">
      {body_xml}
    </u:{action}>
  </s:Body>
</s:Envelope>""".encode("utf-8")

    headers = {
        "Content-Type": 'text/xml; charset="utf-8"',
        "SOAPAction": f'"{service_type}#{action}"',
        "User-Agent": "upnp-igd-tester/0.1",
    }

    req = urllib.request.Request(
        control_url, data=envelope, headers=headers, method="POST"
    )

    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        status_code = resp.getcode()
        body = resp.read()
    except urllib.error.HTTPError as e:
        status_code = e.code
        body = e.read()
    except urllib.error.URLError as e:
        raise TestError(f"HTTP error when calling {action}: {e}") from e

    if status_code != 200:
        # SOAP Fault 情況
        try:
            root = ET.fromstring(body)
            err_code = root.find(".//errorCode")
            err_desc = root.find(".//errorDescription")
            code_text = err_code.text if err_code is not None else "unknown"
            desc_text = err_desc.text if err_desc is not None else ""
            raise TestError(f"SOAP fault {code_text}: {desc_text}")
        except ET.ParseError:
            raise TestError(f"HTTP {status_code} from IGD, body: {body[:200]!r}")

    # HTTP 200，試著用正式 XML parser
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        if action == "GetSpecificPortMappingEntry":
            debug("DEBUG: XML parse error in GetSpecificPortMappingEntry response, raw body:")
            debug(body[:500].decode("utf-8", errors="replace"))
            # 用 fallback parser 再試一次
            fallback = fallback_parse_getspecific(body)
            debug(f"DEBUG: fallback parsed fields: {fallback}")
            return fallback
        # 其他 action 就算了，回空 dict
        return {}

    resp_tag_suffix = f"{action}Response"
    result: Dict[str, str] = {}
    for elem in root.iter():
        tag = strip_ns(elem.tag)
        if tag == resp_tag_suffix:
            for child in elem:
                child_tag = strip_ns(child.tag)
                result[child_tag] = (child.text or "")
            break

    # 若是 GetSpecificPortMappingEntry，結果又是空 dict，也啟用 fallback
    if action == "GetSpecificPortMappingEntry" and not result:
        debug("DEBUG: Empty XML result for GetSpecificPortMappingEntry, raw body:")
        debug(body[:500].decode("utf-8", errors="replace"))
        fallback = fallback_parse_getspecific(body)
        debug(f"DEBUG: fallback parsed fields: {fallback}")
        return fallback

    return result


def pick_best_device(
    discovered: List[Tuple[Tuple[str, int], Dict[str, str], str]],
    target_ip: Optional[str],
) -> str:
    """從 SSDP 結果中挑一個 IGD 裝置，回傳 LOCATION。"""
    if not discovered:
        raise TestError("SSDP 沒找到任何裝置。")

    candidates = []
    for (addr, headers, raw) in discovered:
        location = headers.get("location")
        st = headers.get("st", "")
        usn = headers.get("usn", "")
        server = headers.get("server", "")
        host = None
        if location:
            try:
                parsed = urllib.parse.urlparse(location)
                host = parsed.hostname
            except Exception:
                host = None
        candidates.append(
            {
                "addr": addr,
                "headers": headers,
                "raw": raw,
                "location": location,
                "st": st,
                "usn": usn,
                "server": server,
                "host": host,
            }
        )

    def log_device(prefix: str, c: dict) -> None:
        log(
            f"{prefix} {c['addr'][0]}  ST={c['st']}  USN={c['usn']}  "
            f"LOCATION={c['location']}  SERVER={c['server']}"
        )

    if target_ip:
        for c in candidates:
            if c["host"] == target_ip:
                log_device("Selected (target-ip match):", c)
                if not c["location"]:
                    raise TestError("選中的裝置缺 LOCATION header。")
                return c["location"]

    for c in candidates:
        if "InternetGatewayDevice" in (c["st"] or "") or "InternetGatewayDevice" in (
            c["usn"] or ""
        ):
            log_device("Selected (IGD match):", c)
            if not c["location"]:
                raise TestError("選中的 IGD 裝置缺 LOCATION header。")
            return c["location"]

    c = candidates[0]
    log_device("Selected (fallback first):", c)
    if not c["location"]:
        raise TestError("fallback 裝置缺 LOCATION header。")
    return c["location"]


def run_tests(
    iface: str, target_ip: Optional[str], test_port: int, protocol: str
) -> None:
    """主流程：SSDP → IGD → Test1/2。"""
    proto = protocol.upper()
    if proto not in ("TCP", "UDP"):
        raise ValueError("protocol 必須是 TCP 或 UDP")

    local_ip = get_ipv4_for_interface(iface)
    log(f"Using interface {iface} with IP {local_ip}")

    discovered = ssdp_discover(local_ip, timeout=3.0, st="ssdp:all")
    log(f"Discovered {len(discovered)} device(s) via SSDP.")

    if not discovered:
        raise TestError("SSDP 沒找到任何裝置。")

    location = pick_best_device(discovered, target_ip=target_ip)
    service_type, control_url, event_url, scpd_url, base_url = find_igd_device(location)
    if not control_url:
        raise TestError("IGD service 缺 controlURL。")

    # Test 1
    log("=== Test 1: GetExternalIPAddress ===")
    try:
        res = soap_action(control_url, service_type, "GetExternalIPAddress")
        external_ip = res.get("NewExternalIPAddress", "")
        log(f"External IP reported by IGD: {external_ip}")
    except TestError as e:
        log(f"GetExternalIPAddress FAILED: {e}")
        raise

    # Test 2
    log("=== Test 2: Port Mapping (Add/GetSpecific/Delete) ===")
    desc = "upnp_igd_tester_entry"
    internal_client = local_ip

    log(f"Trying to delete any existing mapping on {test_port}/{proto} (ignore errors).")
    try:
        soap_action(
            control_url,
            service_type,
            "DeletePortMapping",
            {
                "NewRemoteHost": "",
                "NewExternalPort": test_port,
                "NewProtocol": proto,
            },
        )
        log("Old mapping deleted (or IGD accepted delete).")
    except TestError as e:
        if DEBUG:
            log(f"DeletePortMapping (pre-clean) returned error (ignored): {e}")
        else:
            log("DeletePortMapping (pre-clean): no existing mapping or CPE fault (ignored).")

    log(
        f"Adding port mapping: external {test_port}/{proto} "
        f"-> internal {internal_client}:{test_port} ({desc}), lease 0."
    )
    try:
        soap_action(
            control_url,
            service_type,
            "AddPortMapping",
            {
                "NewRemoteHost": "",
                "NewExternalPort": test_port,
                "NewProtocol": proto,
                "NewInternalPort": test_port,
                "NewInternalClient": internal_client,
                "NewEnabled": 1,
                "NewPortMappingDescription": desc,
                "NewLeaseDuration": 0,
            },
        )
        log("AddPortMapping succeeded.")
    except TestError as e:
        log(f"AddPortMapping FAILED: {e}")
        raise

    time.sleep(1.0)

    log("Querying mapping via GetSpecificPortMappingEntry (with retry).")
    last_error: Optional[Exception] = None
    max_tries = 3

    for attempt in range(1, max_tries + 1):
        try:
            res = soap_action(
                control_url,
                service_type,
                "GetSpecificPortMappingEntry",
                {
                    "NewRemoteHost": "",
                    "NewExternalPort": test_port,
                    "NewProtocol": proto,
                },
            )
            log(f"GetSpecificPortMappingEntry result (attempt {attempt}): {res}")

            if res:
                ic = res.get("NewInternalClient", "")
                ip = res.get("NewInternalPort", "")
                if ic != internal_client or str(ip) != str(test_port):
                    # 這裡會被 _classify_phase 判成 "port_query_verify"
                    raise TestError(
                        f"Mapping mismatch, expected {internal_client}:{test_port}, got {ic}:{ip}"
                    )
                log("Port mapping verification PASSED.")
                last_error = None
                break
            else:
                last_error = TestError(
                    "Empty result from GetSpecificPortMappingEntry (mapping not visible?)."
                )
        except TestError as e:
            log(f"GetSpecificPortMappingEntry FAILED on attempt {attempt}: {e}")
            last_error = e

        if attempt < max_tries:
            log("Retrying GetSpecificPortMappingEntry in 1 second...")
            time.sleep(1.0)

    if last_error is not None:
        raise last_error

    log("Deleting test port mapping.")
    try:
        soap_action(
            control_url,
            service_type,
            "DeletePortMapping",
            {
                "NewRemoteHost": "",
                "NewExternalPort": test_port,
                "NewProtocol": proto,
            },
        )
        log("DeletePortMapping succeeded.")
    except TestError as e:
        log(f"DeletePortMapping (cleanup) FAILED: {e}")
        # 把 cleanup 也視為失敗狀況
        raise


def run_upnp_igd_test(
    iface: str,
    target_ip: Optional[str] = None,
    test_port: int = 54321,
    protocol: str = "TCP",
) -> Dict[str, Any]:
    """
    給其他 Python 腳本呼叫的入口。

    回傳 dict：
      {
        "ok": True/False,  # 測試是否通過
        "phase": "ok" | "ssdp" | "get_external_ip" |
                 "port_add" | "port_query" | "port_query_verify" |
                 "port_delete" | "other" | "unexpected",
        "reason": "<錯誤訊息字串>"
      }
    """
    try:
        run_tests(iface, target_ip, test_port, protocol)
        return {
            "ok": True,
            "phase": "ok",
            "reason": "",
        }
    except TestError as e:
        msg = str(e)
        phase = _classify_phase(msg)
        return {
            "ok": False,
            "phase": phase,
            "reason": msg,
        }
    except Exception as e:
        # 非預期錯誤，一樣回傳給 caller，但 phase 標成 "unexpected"
        return {
            "ok": False,
            "phase": "unexpected",
            "reason": str(e),
        }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Basic UPnP IGD tester (SSDP + GetExternalIPAddress + PortMapping)."
    )
    parser.add_argument(
        "--iface",
        default=DEFAULT_IFACE,
        help=f"要用來送 SSDP 的 Linux 介面名稱 (default: {DEFAULT_IFACE})",
    )
    parser.add_argument(
        "--target-ip",
        help=(
            "偏好選用的 IGD 目標 IP (LOCATION 裡的 host)。"
            "若網段有多台 UPnP 裝置，建議指定 CPE 的 IP。"
        ),
    )
    parser.add_argument(
        "--port",
        type=int,
        default=54321,
        help="測試用的 port (default: 54321)",
    )
    parser.add_argument(
        "--protocol",
        choices=["TCP", "UDP"],
        default="TCP",
        help="Port mapping 測試用協定 (default: TCP)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="啟用 debug 訊息（包含 pre-clean 錯誤細節與 SOAP fallback log）",
    )

    args = parser.parse_args(argv)

    # 設定全域 DEBUG flag
    global DEBUG
    DEBUG = args.debug

    result = run_upnp_igd_test(
        iface=args.iface,
        target_ip=args.target_ip,
        test_port=args.port,
        protocol=args.protocol,
    )

    # 印一行 JSON，方便外部腳本 (shell / runner) parse
    print(
        json.dumps(
            {
                "event": "upnp-igd-tester-result",
                "iface": args.iface,
                "target_ip": args.target_ip,
                "port": args.port,
                "protocol": args.protocol,
                "ok": result["ok"],
                "phase": result["phase"],
                "reason": result["reason"],
            },
            ensure_ascii=False,
        )
    )

    if result["ok"]:
        log("TEST PASSED.")
        return 0
    elif result["phase"] == "unexpected":
        log(f"UNEXPECTED ERROR: {result['reason']}")
        return 2
    else:
        log(f"TEST FAILED ({result['phase']}): {result['reason']}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

