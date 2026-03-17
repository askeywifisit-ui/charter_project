#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
noc_api_cli.py — NOC/INT API CLI（無互動、可參數化）

Features:
  - login (get token)
  - node-id (auto via cpe_metrics_agent_serial.py, prints plain node id)
  - ssh-enable / ssh-disable (kvConfigs)
  - wifi-status / wifi-enable / wifi-disable (location scoped)
  - lte-status / lte-enable / lte-disable (location scoped)
  - speedtest-run / speedtest-results / speedtest-result (location+node scoped)
  - get-location (resolve locationId from nodeId)
  - dhcp-resv-list / dhcp-resv-get / dhcp-resv-set / dhcp-resv-del (DHCP Reservation)

Defaults:
  BASE         = https://piranha-int.tau.dev-charter.net
  CUSTOMER_ID  = 682d4e5179b80027cd6fb27e  (override with --customer-id or env CUSTOMER_ID)

Requires: requests
  pip install requests
"""
import argparse
import json
import os
import sys
import time
import subprocess
import re
from typing import Tuple, Optional, List
from urllib.parse import quote

import requests

DEFAULT_BASE = os.environ.get("BASE", "https://piranha-int.tau.dev-charter.net")
DEFAULT_CUSTOMER_ID = os.environ.get("CUSTOMER_ID", "682d4e5179b80027cd6fb27e")
# DEFAULT_TIMEOUT: NOC HTTP requests timeout (seconds)
# - override with env: NOC_HTTP_TIMEOUT_SEC or NOC_REQUEST_TIMEOUT_SEC
DEFAULT_TIMEOUT = int(os.environ.get("NOC_HTTP_TIMEOUT_SEC", os.environ.get("NOC_REQUEST_TIMEOUT_SEC", "20")))

# ----------------- HTTP helpers -----------------
def req(method, url, token: str = "", *, bearer: bool = False, insecure: bool = False, **kwargs) -> requests.Response:
    headers = kwargs.pop("headers", {})
    if "Content-Type" not in headers:
        headers["Content-Type"] = "application/json"
    if token and "Authorization" not in headers:
        headers["Authorization"] = (f"Bearer {token}" if bearer else token)
    r = requests.request(method, url, headers=headers, timeout=DEFAULT_TIMEOUT, verify=not insecure, **kwargs)
    r.raise_for_status()
    return r

def req_retry_412(
    method,
    url,
    token: str = "",
    *,
    bearer: bool = False,
    insecure: bool = False,
    retries: int = 0,
    wait_sec: float = 10.0,
    **kwargs,
) -> requests.Response:
    """
    有些 NOC endpoint 在 prefix 尚未 ready 時會回 HTTP 412（Subnet prefix is unknown）。
    這個 helper 只針對 HTTP 412 做 retry，其它錯誤直接 raise。
    """
    last_exc = None
    for attempt in range(retries + 1):
        try:
            return req(method, url, token, bearer=bearer, insecure=insecure, **kwargs)
        except requests.HTTPError as e:
            last_exc = e
            r = getattr(e, "response", None)
            code = getattr(r, "status_code", None)
            if code == 412 and attempt < retries:
                time.sleep(wait_sec)
                continue
            raise
    raise last_exc  # pragma: no cover



def api(base: str, path: str) -> str:
    base = base.rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    return f"{base}/api{path}"

# ----------------- small utils -----------------
def norm_mac(mac: str) -> str:
    """Normalize MAC to aa:bb:cc:dd:ee:ff (accept aa-bb-.. or aabbccddeeff)."""
    m = (mac or "").strip().lower()
    m = m.replace("-", ":")
    if ":" not in m and len(m) == 12:
        m = ":".join(m[i : i + 2] for i in range(0, 12, 2))
    parts = m.split(":")
    if len(parts) != 6 or any(len(p) != 2 for p in parts):
        raise ValueError(f"invalid mac: {mac}")
    int("".join(parts), 16)  # validate hex
    return m

def mac_path(mac: str) -> str:
    """Encode MAC for safe usage inside URL path segment (':' must be encoded)."""
    return quote(norm_mac(mac), safe="")



# ----------------- API wrappers -----------------
def login(base: str, email: str, password: str, *, bearer: bool = False, insecure: bool = False) -> str:
    r = req(
        "POST",
        api(base, "/Customers/login"),
        json={"email": email, "password": password},
        bearer=bearer,
        insecure=insecure,
    )
    tok = r.json().get("id")
    if not tok:
        raise RuntimeError("login ok but token(id) missing")
    return tok


def get_node(base: str, customer_id: str, node_id: str, *, token: str, bearer: bool = False, insecure: bool = False) -> dict:
    return req(
        "GET",
        api(base, f"/Customers/{customer_id}/nodes/{node_id}"),
        token,
        bearer=bearer,
        insecure=insecure,
    ).json()

def get_location_node(
    base: str,
    customer_id: str,
    location_id: str,
    node_id: str,
    *,
    token: str,
    bearer: bool = False,
    insecure: bool = False,
) -> dict:
    """
    GET /Customers/{id}/locations/{locationId}/nodes/{nodeId}

    取得 location scope 的單一 node 資訊（包含 connectionState、ip、wanIp、
    channel、connectedDeviceCount 等詳細狀態）。
    """
    return req(
        "GET",
        api(base, f"/Customers/{customer_id}/locations/{location_id}/nodes/{node_id}"),
        token,
        bearer=bearer,
        insecure=insecure,
    ).json()


def get_location_id(
    base: str,
    customer_id: str,
    node_id: str,
    *,
    token: str,
    bearer: bool = False,
    insecure: bool = False,
) -> str:
    j = get_node(base, customer_id, node_id, token=token, bearer=bearer, insecure=insecure)
    loc = j.get("locationId")
    if not loc:
        raise RuntimeError("locationId not found for nodeId")
    return loc



# SSH kvConfigs
def kv_url(base: str, customer_id: str, location_id: str, node_id: str) -> str:
    return api(base, f"/Customers/{customer_id}/locations/{location_id}/nodes/{node_id}/kvConfigs")


def ssh_enable(
    base: str,
    customer_id: str,
    location_id: str,
    node_id: str,
    passwd: str,
    timeout_min: int,
    *,
    token: str,
    bearer: bool = False,
    insecure: bool = False,
) -> dict:
    now = str(int(time.time()))
    timeout_sec = str(int(timeout_min) * 60)
    payload = {
        "kvConfigs": [
            {"module": "SSHM", "key": "sshTotalSessTimeout", "value": timeout_sec},
            {"module": "SSHM", "key": "sshAuthPasswd", "value": passwd},
            {"module": "SSHM", "key": "sshEnableTime", "value": now},
            {"module": "SSHM", "key": "sshAccessControl", "value": "true"},
        ]
    }
    r = req(
        "PATCH",
        kv_url(base, customer_id, location_id, node_id),
        token,
        bearer=bearer,
        insecure=insecure,
        json=payload,
    )
    return r.json() if r.content else {"ok": True}


def ssh_disable(
    base: str,
    customer_id: str,
    location_id: str,
    node_id: str,
    *,
    token: str,
    bearer: bool = False,
    insecure: bool = False,
) -> dict:
    now = str(int(time.time()))
    payload = {
        "kvConfigs": [
            {"module": "SSHM", "key": "sshAuthPasswd", "value": now},
            {"module": "SSHM", "key": "sshEnableTime", "value": now},
            {"module": "SSHM", "key": "sshAccessControl", "value": "false"},
        ]
    }
    r = req(
        "PATCH",
        kv_url(base, customer_id, location_id, node_id),
        token,
        bearer=bearer,
        insecure=insecure,
        json=payload,
    )
    return r.json() if r.content else {"ok": True}


# Wi-Fi (AP) — enable/disable/status
def wifi_status(
    base: str,
    customer_id: str,
    location_id: str,
    *,
    token: str,
    bearer: bool = False,
    insecure: bool = False,
) -> dict:
    # Try GET /wifiNetwork first (preferred if available)
    url = api(base, f"/Customers/{customer_id}/locations/{location_id}/wifiNetwork")
    try:
        return req("GET", url, token, bearer=bearer, insecure=insecure).json()
    except requests.HTTPError:
        # Fallback to list; caller can inspect content
        url2 = api(base, f"/Customers/{customer_id}/locations/{location_id}/wifiNetworksWithWpaMode")
        return req("GET", url2, token, bearer=bearer, insecure=insecure).json()


def wifi_set_enabled(
    base: str,
    customer_id: str,
    location_id: str,
    enabled: bool,
    *,
    token: str,
    bearer: bool = False,
    insecure: bool = False,
) -> dict:
    url = api(base, f"/Customers/{customer_id}/locations/{location_id}/wifiNetwork")
    payload = {"enabled": bool(enabled)}
    r = req("PATCH", url, token, bearer=bearer, insecure=insecure, json=payload)
    return r.json() if r.content else {"ok": True}


def wifi_network_update(
    base: str,
    customer_id: str,
    location_id: str,
    *,
    token: str,
    bearer: bool = False,
    insecure: bool = False,
    ssid: Optional[str] = None,
    encryption_key: Optional[str] = None,
    wpa_mode: Optional[str] = None,
    wpa_modes: Optional[str] = None,
) -> dict:
    """
    PUT /Customers/{id}/locations/{locationId}/wifiNetwork

    用來更新 Wi-Fi 的 SSID / PSK（encryptionKey），以及選擇性的
    wpaMode / wpaModes。

    只有不是 None 的欄位才會被送出去，所以可以只改 SSID 或只改密碼。
    """
    url = api(base, f"/Customers/{customer_id}/locations/{location_id}/wifiNetwork")
    payload: dict = {}
    if ssid is not None:
        payload["ssid"] = ssid
    if encryption_key is not None:
        payload["encryptionKey"] = encryption_key
    if wpa_mode is not None:
        payload["wpaMode"] = wpa_mode
    if wpa_modes is not None:
        payload["wpaModes"] = wpa_modes

    if not payload:
        raise ValueError(
            "wifi_network_update: 必須至少指定 ssid / encryption_key / wpa_mode / wpa_modes 其中一個"
        )

    r = req("PUT", url, token, bearer=bearer, insecure=insecure, json=payload)
    return r.json() if r.content else {"ok": True}


def wifi_network_ssid(
    base: str,
    customer_id: str,
    location_id: str,
    *,
    token: str,
    bearer: bool = False,
    insecure: bool = False,
) -> dict:
    """
    GET /Customers/{id}/locations/{locationId}/wifiNetwork/ssid

    只查 SSID 的便利函式，回傳格式通常是:
      { "ssid": "xxxx" }
    """
    url = api(base, f"/Customers/{customer_id}/locations/{location_id}/wifiNetwork/ssid")
    r = req("GET", url, token, bearer=bearer, insecure=insecure)
    return r.json()


# UPNP — get/set (location scoped)
def upnp_status(
    base: str,
    customer_id: str,
    location_id: str,
    *,
    token: str,
    bearer: bool = False,
    insecure: bool = False,
) -> dict:
    """
    GET /Customers/{id}/locations/{locationId}/networkConfiguration/upnp
    回傳目前的 UPNP 設定，例如:
    {
      "enabled": false,
      "mode": "disable",
      "modeRealized": true
    }
    """
    url = api(base, f"/Customers/{customer_id}/locations/{location_id}/networkConfiguration/upnp")
    r = req("GET", url, token, bearer=bearer, insecure=insecure)
    return r.json()


def upnp_set(
    base: str,
    customer_id: str,
    location_id: str,
    *,
    enabled: Optional[bool] = None,
    mode: Optional[str] = None,
    token: str,
    bearer: bool = False,
    insecure: bool = False,
) -> dict:
    """
    PUT /Customers/{id}/locations/{locationId}/networkConfiguration/upnp

    enabled: 舊欄位，當 bool 用
    mode:    "enable" / "disable" / "auto" (swagger 寫 Auto，這裡統一轉成小寫)
    """
    if enabled is None and mode is None:
        raise ValueError("upnp_set: 必須至少指定 enabled 或 mode")

    payload: dict = {}
    if enabled is not None:
        payload["enabled"] = bool(enabled)
    if mode is not None:
        m = str(mode).strip()
        if m.lower() == "auto":
            m = "auto"
        payload["mode"] = m

    url = api(base, f"/Customers/{customer_id}/locations/{location_id}/networkConfiguration/upnp")
    r = req("PUT", url, token, bearer=bearer, insecure=insecure, json=payload)
    return r.json() if r.content else {"ok": True}


# (選配) Sniffing 狀態：DNS/HTTP/UPnP/mDNS
def sniffing_status(
    base: str,
    customer_id: str,
    location_id: str,
    *,
    token: str,
    bearer: bool = False,
    insecure: bool = False,
) -> dict:
    """
    GET /Customers/{id}/locations/{locationId}/sniffing
    取得 DNS/HTTP/UPnP/mDNS sniffing toggles 狀態。
    """
    url = api(base, f"/Customers/{customer_id}/locations/{location_id}/sniffing")
    r = req("GET", url, token, bearer=bearer, insecure=insecure)
    return r.json()



# DHCP Reservations — create/get/list/delete (location scoped)
def dhcp_resv_list(
    base: str,
    customer_id: str,
    location_id: str,
    *,
    token: str,
    bearer: bool = False,
    insecure: bool = False,
    retry_412: int = 0,
    retry_wait: float = 10.0,
) -> dict:
    """GET /Customers/{id}/locations/{locationId}/networkConfiguration/dhcpReservations"""
    url = api(base, f"/Customers/{customer_id}/locations/{location_id}/networkConfiguration/dhcpReservations")
    r = req_retry_412(
        "GET",
        url,
        token,
        bearer=bearer,
        insecure=insecure,
        retries=retry_412,
        wait_sec=retry_wait,
    )
    return r.json()


def dhcp_resv_get(
    base: str,
    customer_id: str,
    location_id: str,
    mac: str,
    *,
    token: str,
    bearer: bool = False,
    insecure: bool = False,
    retry_412: int = 0,
    retry_wait: float = 10.0,
) -> dict:
    """GET /Customers/{id}/locations/{locationId}/networkConfiguration/dhcpReservations/{mac}"""
    url = api(
        base,
        f"/Customers/{customer_id}/locations/{location_id}/networkConfiguration/dhcpReservations/{mac_path(mac)}",
    )
    r = req_retry_412(
        "GET",
        url,
        token,
        bearer=bearer,
        insecure=insecure,
        retries=retry_412,
        wait_sec=retry_wait,
    )
    return r.json()


def dhcp_resv_set(
    base: str,
    customer_id: str,
    location_id: str,
    mac: str,
    ip: str,
    host_name: Optional[str] = None,
    *,
    token: str,
    bearer: bool = False,
    insecure: bool = False,
    retry_412: int = 0,
    retry_wait: float = 10.0,
) -> dict:
    """
    PUT /Customers/{id}/locations/{locationId}/networkConfiguration/dhcpReservations/{mac}
    Content-Type: application/x-www-form-urlencoded
    formData: ip (required), hostName (optional)
    """
    url = api(
        base,
        f"/Customers/{customer_id}/locations/{location_id}/networkConfiguration/dhcpReservations/{mac_path(mac)}",
    )
    data = {"ip": str(ip)}
    if host_name:
        data["hostName"] = str(host_name)
    r = req_retry_412(
        "PUT",
        url,
        token,
        bearer=bearer,
        insecure=insecure,
        retries=retry_412,
        wait_sec=retry_wait,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=data,
    )
    return r.json() if r.content else {"ok": True}


def dhcp_resv_del(
    base: str,
    customer_id: str,
    location_id: str,
    mac: str,
    *,
    token: str,
    bearer: bool = False,
    insecure: bool = False,
    retry_412: int = 0,
    retry_wait: float = 10.0,
) -> dict:
    """DELETE /Customers/{id}/locations/{locationId}/networkConfiguration/dhcpReservations/{mac}"""
    url = api(
        base,
        f"/Customers/{customer_id}/locations/{location_id}/networkConfiguration/dhcpReservations/{mac_path(mac)}",
    )
    r = req_retry_412(
        "DELETE",
        url,
        token,
        bearer=bearer,
        insecure=insecure,
        retries=retry_412,
        wait_sec=retry_wait,
    )
    return r.json() if r.content else {"ok": True}

# LTE — enable/disable/status (note: lteservice root, not /api)
def lte_root(base: str) -> str:
    return base.rstrip("/") + "/lteservice"


def lte_status(
    base: str,
    location_id: str,
    *,
    token: str,
    bearer: bool = False,
    insecure: bool = False,
) -> dict:
    url = f"{lte_root(base)}/locations/{location_id}/configuration"
    return req("GET", url, token, bearer=bearer, insecure=insecure).json()


def lte_enable(
    base: str,
    location_id: str,
    *,
    token: str,
    bearer: bool = False,
    insecure: bool = False,
) -> dict:
    url = f"{lte_root(base)}/locations/{location_id}/enable"
    r = req("POST", url, token, bearer=bearer, insecure=insecure)
    return r.json() if r.content else {"ok": True}


def lte_disable(
    base: str,
    location_id: str,
    *,
    token: str,
    bearer: bool = False,
    insecure: bool = False,
) -> dict:
    url = f"{lte_root(base)}/locations/{location_id}/disable"
    r = req("POST", url, token, bearer=bearer, insecure=insecure)
    return r.json() if r.content else {"ok": True}


# SpeedTest — run & query
def speedtest_run(
    base: str,
    customer_id: str,
    location_id: str,
    node_id: str,
    *,
    token: str,
    bearer: bool = False,
    insecure: bool = False,
    body: Optional[dict] = None,
) -> dict:
    """
    POST /Customers/{id}/locations/{locationId}/nodes/{nodeId}/speedTest
    觸發一個新的 speed test。
    """
    url = api(base, f"/Customers/{customer_id}/locations/{location_id}/nodes/{node_id}/speedTest")
    payload = body or {}
    r = req("POST", url, token, bearer=bearer, insecure=insecure, json=payload)
    return r.json() if r.content else {"ok": True}


def speedtest_results(
    base: str,
    customer_id: str,
    location_id: str,
    node_id: str,
    *,
    token: str,
    bearer: bool = False,
    insecure: bool = False,
) -> dict:
    """
    GET /Customers/{id}/locations/{locationId}/nodes/{nodeId}/speedTestResults
    取得該 node 全部 speed test 結果列表。
    """
    url = api(base, f"/Customers/{customer_id}/locations/{location_id}/nodes/{node_id}/speedTestResults")
    r = req("GET", url, token, bearer=bearer, insecure=insecure)
    return r.json()


def speedtest_result_by_id(
    base: str,
    customer_id: str,
    location_id: str,
    node_id: str,
    request_id: str,
    *,
    token: str,
    bearer: bool = False,
    insecure: bool = False,
) -> dict:
    """
    GET /Customers/{id}/locations/{locationId}/nodes/{nodeId}/speedTestResults/{requestId}
    依 requestId 取得單一 speed test 結果。
    """
    url = api(
        base,
        f"/Customers/{customer_id}/locations/{location_id}/nodes/{node_id}/speedTestResults/{request_id}",
    )
    r = req("GET", url, token, bearer=bearer, insecure=insecure)
    return r.json()


def reboot_node(
    base: str,
    customer_id: str,
    location_id: str,
    node_id: str,
    *,
    token: str,
    bearer: bool = False,
    insecure: bool = False,
    delay: Optional[float] = None,
) -> dict:
    """
    PUT /Customers/{id}/locations/{locationId}/nodes/{nodeId}/reboot

    delay: reboot delay in seconds (form data). If None, omit to use server default.
    """
    url = api(base, f"/Customers/{customer_id}/locations/{location_id}/nodes/{node_id}/reboot")
    data = {}
    if delay is not None:
        # API 定義為 formData number(double)；用字串避免型別問題
        data["delay"] = str(delay)
    r = req(
        "PUT",
        url,
        token,
        bearer=bearer,
        insecure=insecure,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=data or None,
    )
    # 多數情況 reboot API 不會有 body；若有就回傳 JSON
    return r.json() if r.content else {"ok": True}


# ----------------- factory reset  ---------------------------
def factory_reset(
    base: str,
    customer_id: str,
    location_id: str,
    *,
    token: str,
    bearer: bool = False,
    insecure: bool = False,
    options: Optional[dict] = None,
) -> dict:
    """
    DELETE /Customers/{id}/locations/{locationId}/factoryReset

    options 行為：
      - options is None  → 往後相容：10 個欄位全部 True（完整 Factory Reset）
      - options 是 {}    → 送出空 payload（特殊測試用，不重置任何項目）
      - options 有內容   → 僅重置 options 裡為 True 的欄位

    對應 swagger / NOC API 的欄位：
      persons
      onboardingCheckpoints
      devices
      networkConfiguration
      wifiNetwork
      secondaryNetworks
      deviceFreeze
      deviceNicknames
      managers
      wanConfiguration
    """
    url = api(base, f"/Customers/{customer_id}/locations/{location_id}/factoryReset")

    if options is None:
        # 向後相容：沒指定 options 就做「全選」
        payload = {
            "persons": True,
            "onboardingCheckpoints": True,
            "devices": True,
            "networkConfiguration": True,
            "wifiNetwork": True,
            "secondaryNetworks": True,
            "deviceFreeze": True,
            "deviceNicknames": True,
            "managers": True,
            "wanConfiguration": True,
        }
    else:
        # 包含 {}（空 payload）或部分欄位
        payload = options

    r = req(
        "DELETE",
        url,
        token,
        bearer=bearer,
        insecure=insecure,
        json=payload,
    )
    return r.json() if r.content else {"ok": True}


# ----------------- serial node-id (metrics) -----------------
ANSI_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")


def strip_ansi(s: str) -> str:
    return ANSI_RE.sub("", s)


def parse_node_id_from_text(text: str) -> str:
    text = strip_ansi(text or "")
    # Prefer lines like "id : <hex>"
    for line in text.splitlines():
        m = re.search(r"\bid\s*[:=]\s*([0-9a-f]{10,})\b", line, re.I)
        if m:
            return m.group(1).lower()
    # Fallback: first long hex token
    m = re.search(r"\b([0-9a-f]{10,})\b", text, re.I)
    if m:
        return m.group(1).lower()
    raise RuntimeError("node-id not found in serial output")


def run_serial_metrics(
    script_path: str,
    device: str,
    baud: int,
    user: str,
    password: str,
) -> Tuple[int, str, str]:
    # Always invoke via current python to avoid permission issues
    args = [
        sys.executable,
        script_path,
        "--device",
        device,
        "--baud",
        str(baud),
        "--user",
        user,
        "--cmd",
        "node-id",
    ]
    if password:
        args += ["--password", password]
    p = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=60,
    )
    return p.returncode, p.stdout, p.stderr


def serial_get_node_id(
    script_metrics: str,
    device: str,
    baud: int,
    user: str,
    password: str,
) -> str:
    if not os.path.exists(script_metrics):
        raise RuntimeError(f"serial metrics script not found: {script_metrics}")
    rc, out, err = run_serial_metrics(script_metrics, device, baud, user, password)
    if rc != 0:
        raise RuntimeError(f"serial metrics failed rc={rc}: {err.strip()}")
    return parse_node_id_from_text((out or "") + "\n" + (err or ""))


# ----------------- CLI -----------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="NOC API CLI (no-interactive) with auto node-id (metrics)",
    )
    p.add_argument("--base", default=DEFAULT_BASE)
    p.add_argument("--customer-id", default=DEFAULT_CUSTOMER_ID)
    p.add_argument("--token")
    p.add_argument("--email")
    p.add_argument("--password")
    p.add_argument("--bearer", action="store_true", help="Use Bearer <token> auth header")
    p.add_argument("--insecure", action="store_true", help="Skip TLS verification")
   
    # serial (metrics) options
    p.add_argument(
        "--serial-metrics",
        default=os.environ.get("SERIAL_METRICS", "./cpe_metrics_agent_serial.py"),
        help="Path to cpe_metrics_agent_serial.py",
    )
    p.add_argument("--serial-device", help="Serial device, e.g. /dev/ttyUSB0")
    p.add_argument(
        "--serial-baud",
        type=int,
        default=int(os.environ.get("SERIAL_BAUD", "115200")),
    )
    p.add_argument(
        "--serial-user",
        default=os.environ.get("SERIAL_USER", "root"),
    )
    p.add_argument(
        "--serial-password",
        default=os.environ.get("SERIAL_PASSWORD", ""),
    )

    sub = p.add_subparsers(dest="cmd", required=True)

    # login
    sub.add_parser("login", help="Login and print token")
    
    # Print node-id (via serial metrics)
    sub.add_parser("node-id", help="Get node-id via serial metrics (cpe_metrics_agent_serial.py)")
    
    # node status
    sp = sub.add_parser("node-status", help="Get node info from /locations/{locationId}/nodes/{nodeId}")
    sp.add_argument("--node-id", help="Node ID (if omitted, use serial-metrics)")
    sp.add_argument("--location-id", help="Location ID (if omitted, auto resolve from node-id)")


    # SSH
    sp = sub.add_parser("ssh-enable", help="Enable SSH via kvConfigs")
    sp.add_argument("--node-id", help="Node ID (if omitted, use serial-metrics)")
    sp.add_argument("--location-id", help="Location ID (if omitted, auto resolve from node-id)")
    sp.add_argument("--ssh-pass", required=True, help="SSH password to set")
    sp.add_argument("--timeout-min", type=int, default=120, help="SSH session timeout (minutes)")

    sp = sub.add_parser("ssh-disable", help="Disable SSH via kvConfigs")
    sp.add_argument("--node-id")
    sp.add_argument("--location-id")

    # Wi-Fi
    sp = sub.add_parser("wifi-status", help="Get Wi-Fi status for a location")
    sp.add_argument("--location-id")

    sp = sub.add_parser("wifi-enable", help="Enable Wi-Fi for a location")
    sp.add_argument("--location-id")

    sp = sub.add_parser("wifi-disable", help="Disable Wi-Fi for a location")
    sp.add_argument("--location-id")
    
    # Wi-Fi config (SSID / password)
    sp = sub.add_parser("wifi-config-set", help="Update Wi-Fi SSID / PSK for a location")
    sp.add_argument("--location-id", help="Location ID (if omitted, auto resolve from node-id / serial)")
    sp.add_argument("--node-id", help="Node ID (optional，沒給就走 serial metrics)")
    sp.add_argument("--ssid", help="New Wi-Fi SSID")
    sp.add_argument("--passphrase", help="New Wi-Fi password / PSK")
    sp.add_argument("--wpa-mode", dest="wpa_mode", help="Optional WPA mode string (e.g. WPA2-PSK)")
    sp.add_argument("--wpa-modes", dest="wpa_modes", help="Optional raw wpaModes string (進階用)")

    sp = sub.add_parser("wifi-ssid", help="Get Wi-Fi SSID for a location")
    sp.add_argument("--location-id", help="Location ID (if omitted, auto resolve from node-id / serial)")
    sp.add_argument("--node-id", help="Node ID (optional，沒給就走 serial metrics)")
    
    # UPNP
    sp = sub.add_parser("upnp-status", help="Get UPNP status for a location")
    sp.add_argument("--location-id")

    sp = sub.add_parser("upnp-set", help="Set UPNP mode/enabled for a location")
    sp.add_argument("--location-id")
    sp.add_argument(
        "--mode",
        choices=["enable", "disable", "auto", "Auto"],
        help="UPNP mode: enable / disable / auto",
    )
    sp.add_argument(
        "--enabled",
        choices=["true", "false", "1", "0"],
        help="(optional) legacy enabled flag",
    )

    sp = sub.add_parser("upnp-enable", help="Shortcut: set UPNP to enable")
    sp.add_argument("--location-id")

    sp = sub.add_parser("upnp-disable", help="Shortcut: set UPNP to disable")
    sp.add_argument("--location-id")

    sp = sub.add_parser("upnp-auto", help="Shortcut: set UPNP to auto")
    sp.add_argument("--location-id")

    
    # LTE
    sp = sub.add_parser("lte-status", help="Get LTE status for a location")
    sp.add_argument("--location-id")

    sp = sub.add_parser("lte-enable", help="Enable LTE for a location")
    sp.add_argument("--location-id")

    sp = sub.add_parser("lte-disable", help="Disable LTE for a location")
    sp.add_argument("--location-id")

    # SpeedTest
    sp = sub.add_parser("speedtest-run", help="Trigger a speed test for a node")
    sp.add_argument("--node-id", help="Node ID (if omitted, use serial-metrics)")
    sp.add_argument("--location-id", help="Location ID (if omitted, auto resolve from node-id)")

    sp = sub.add_parser("speedtest-results", help="List speed test results for a node")
    sp.add_argument("--node-id")
    sp.add_argument("--location-id")

    sp = sub.add_parser("speedtest-result", help="Get a specific speed test result by requestId")
    sp.add_argument("--node-id")
    sp.add_argument("--location-id")
    sp.add_argument("--request-id", required=True)

    # reboot
    sp = sub.add_parser("reboot", help="Reboot a node via NOC API")
    sp.add_argument("--node-id", help="Node ID (if omitted, use serial-metrics)")
    sp.add_argument("--location-id", help="Location ID (if omitted, auto resolve from node-id)")
    sp.add_argument(
        "--delay",
        type=float,
        help="Reboot delay in seconds (if omitted, use server default)",
    )
    
    # Factory Reset
    sp = sub.add_parser("factory-reset", help="Factory reset a location via NOC API")
    sp.add_argument("--node-id", help="Node ID (if omitted, use serial-metrics)")
    sp.add_argument("--location-id", help="Location ID (if omitted, auto resolve from node-id)")
    sp.add_argument(
        "--all",
        action="store_true",
        help="Reset all items (default 行為，沒指定任何欄位也視為 all)",
    )
    sp.add_argument(
        "--empty",
        action="store_true",
        help="送出空 payload {}（不重置任何項目，僅供特殊測試用）",
    )
    # 個別項目開關（僅有被指定的才會出現在 payload 裡，值為 true）
    sp.add_argument("--persons", action="store_true", help="Reset persons")
    sp.add_argument(
        "--onboarding-checkpoints",
        dest="onboarding_checkpoints",
        action="store_true",
        help="Reset onboardingCheckpoints",
    )
    sp.add_argument("--devices", action="store_true", help="Reset devices")
    sp.add_argument(
        "--network-configuration",
        dest="network_configuration",
        action="store_true",
        help="Reset networkConfiguration",
    )
    sp.add_argument(
        "--wifi-network",
        dest="wifi_network",
        action="store_true",
        help="Reset wifiNetwork",
    )
    sp.add_argument(
        "--secondary-networks",
        dest="secondary_networks",
        action="store_true",
        help="Reset secondaryNetworks",
    )
    sp.add_argument(
        "--device-freeze",
        dest="device_freeze",
        action="store_true",
        help="Reset deviceFreeze",
    )
    sp.add_argument(
        "--device-nicknames",
        dest="device_nicknames",
        action="store_true",
        help="Reset deviceNicknames",
    )
    sp.add_argument(
        "--managers",
        action="store_true",
        help="Reset managers",
    )
    sp.add_argument(
        "--wan-configuration",
        dest="wan_configuration",
        action="store_true",
        help="Reset wanConfiguration",
    )


    # DHCP Reservations (location scoped)
    sp = sub.add_parser("dhcp-resv-list", help="List DHCP reservations for a location")
    sp.add_argument("--location-id", help="Location ID (if omitted, auto resolve from node-id)")
    sp.add_argument("--node-id", help="Node ID (optional; if omitted, use serial-metrics)")
    sp.add_argument("--retry-412", type=int, default=0, help="Retry count when HTTP 412 occurs")
    sp.add_argument("--retry-wait", type=float, default=10.0, help="Wait seconds between 412 retries")

    sp = sub.add_parser("dhcp-resv-get", help="Get a DHCP reservation by MAC")
    sp.add_argument("--mac", required=True, help="Target MAC")
    sp.add_argument("--location-id", help="Location ID (if omitted, auto resolve from node-id)")
    sp.add_argument("--node-id", help="Node ID (optional; if omitted, use serial-metrics)")
    sp.add_argument("--retry-412", type=int, default=0)
    sp.add_argument("--retry-wait", type=float, default=10.0)

    sp = sub.add_parser("dhcp-resv-set", help="Create/Update a DHCP reservation (MAC -> IP)")
    sp.add_argument("--mac", required=True, help="Target MAC")
    sp.add_argument("--ip", required=True, help="Reserved IPv4")
    sp.add_argument("--host-name", dest="host_name", help="Optional hostName")
    sp.add_argument("--location-id", help="Location ID (if omitted, auto resolve from node-id)")
    sp.add_argument("--node-id", help="Node ID (optional; if omitted, use serial-metrics)")
    sp.add_argument("--retry-412", type=int, default=0)
    sp.add_argument("--retry-wait", type=float, default=10.0)

    sp = sub.add_parser("dhcp-resv-del", help="Delete a DHCP reservation by MAC")
    sp.add_argument("--mac", required=True, help="Target MAC")
    sp.add_argument("--location-id", help="Location ID (if omitted, auto resolve from node-id)")
    sp.add_argument("--node-id", help="Node ID (optional; if omitted, use serial-metrics)")
    sp.add_argument("--retry-412", type=int, default=0)
    sp.add_argument("--retry-wait", type=float, default=10.0)

    # helpers
    sp = sub.add_parser("get-location", help="Resolve location-id from node-id")
    sp.add_argument("--node-id")

    return p.parse_args()


def ensure_token(args: argparse.Namespace) -> str:
    if args.token:
        return args.token
    if not (args.email and args.password):
        raise SystemExit("需要 --token 或 (--email 與 --password)")
    return login(args.base, args.email, args.password, bearer=args.bearer, insecure=args.insecure)


def resolve_node_id(args: argparse.Namespace) -> str:
    node_id = getattr(args, "node_id", None)
    if node_id:
        return node_id
    if not args.serial_device:
        raise SystemExit("缺少 --node-id；或提供 --serial-device/--serial-baud/--serial-user 以自動取得")
    return serial_get_node_id(
        args.serial_metrics,
        args.serial_device,
        args.serial_baud,
        args.serial_user,
        args.serial_password,
    )


def resolve_location_id(args: argparse.Namespace, node_id: Optional[str], token: str) -> str:
    location_id = getattr(args, "location_id", None)
    if location_id:
        return location_id
    if not node_id:
        node_id = resolve_node_id(args)
    return get_location_id(
        args.base,
        args.customer_id,
        node_id,
        token=token,
        bearer=args.bearer,
        insecure=args.insecure,
    )


def main() -> None:
    args = parse_args()
    tok = ensure_token(args)

    if args.cmd == "login":
        print(tok)
        return

    if args.cmd == "node-id":
        if not args.serial_device:
            raise SystemExit("缺少 --serial-device/--serial-baud/--serial-user 以從 serial 抓取 node-id")
        nid = serial_get_node_id(
            args.serial_metrics,
            args.serial_device,
            args.serial_baud,
            args.serial_user,
            args.serial_password,
        )
        print(nid)
        return
        
    if args.cmd == "node-status":
        # 1. 先決定 node-id（可以用參數或走 serial 自動抓）
        nid = resolve_node_id(args)
        # 2. 再決定 location-id（可以參數給，沒給就從 node 查）
        loc = resolve_location_id(args, nid, tok)

        # 3. 呼叫剛剛新增的 get_location_node()
        node = get_location_node(
            args.base,
            args.customer_id,
            loc,
            nid,
            token=tok,
            bearer=args.bearer,
            insecure=args.insecure,
        )

        # 4. 直接把完整 JSON 印出來，供你 script / jq 處理
        print(json.dumps(node, indent=2, ensure_ascii=False))
        return
    
    if args.cmd == "ssh-enable":
        nid = resolve_node_id(args)
        loc = resolve_location_id(args, nid, tok)
        print(
            json.dumps(
                ssh_enable(
                    args.base,
                    args.customer_id,
                    loc,
                    nid,
                    args.ssh_pass,
                    args.timeout_min,
                    token=tok,
                    bearer=args.bearer,
                    insecure=args.insecure,
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if args.cmd == "ssh-disable":
        nid = resolve_node_id(args)
        loc = resolve_location_id(args, nid, tok)
        print(
            json.dumps(
                ssh_disable(
                    args.base,
                    args.customer_id,
                    loc,
                    nid,
                    token=tok,
                    bearer=args.bearer,
                    insecure=args.insecure,
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if args.cmd == "wifi-status":
        loc = resolve_location_id(args, None, tok)
        print(
            json.dumps(
                wifi_status(
                    args.base,
                    args.customer_id,
                    loc,
                    token=tok,
                    bearer=args.bearer,
                    insecure=args.insecure,
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if args.cmd == "wifi-enable":
        loc = resolve_location_id(args, None, tok)
        print(
            json.dumps(
                wifi_set_enabled(
                    args.base,
                    args.customer_id,
                    loc,
                    True,
                    token=tok,
                    bearer=args.bearer,
                    insecure=args.insecure,
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if args.cmd == "wifi-disable":
        loc = resolve_location_id(args, None, tok)
        print(
            json.dumps(
                wifi_set_enabled(
                    args.base,
                    args.customer_id,
                    loc,
                    False,
                    token=tok,
                    bearer=args.bearer,
                    insecure=args.insecure,
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        return
    
    if args.cmd == "wifi-config-set":
        # 先決定 location-id（可以直接給，或用 node-id / serial 自動解析）
        loc = resolve_location_id(args, getattr(args, "node_id", None), tok)

        if not (args.ssid or args.passphrase or args.wpa_mode or args.wpa_modes):
            raise SystemExit(
                "wifi-config-set: 需要至少指定 --ssid / --passphrase / --wpa-mode / --wpa-modes 其中一項"
            )

        print(
            json.dumps(
                wifi_network_update(
                    args.base,
                    args.customer_id,
                    loc,
                    token=tok,
                    bearer=args.bearer,
                    insecure=args.insecure,
                    ssid=args.ssid,
                    encryption_key=args.passphrase,
                    wpa_mode=args.wpa_mode,
                    wpa_modes=args.wpa_modes,
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if args.cmd == "wifi-ssid":
        loc = resolve_location_id(args, getattr(args, "node_id", None), tok)
        print(
            json.dumps(
                wifi_network_ssid(
                    args.base,
                    args.customer_id,
                    loc,
                    token=tok,
                    bearer=args.bearer,
                    insecure=args.insecure,
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    
    if args.cmd == "upnp-status":
        loc = resolve_location_id(args, None, tok)
        print(
            json.dumps(
                upnp_status(
                    args.base,
                    args.customer_id,
                    loc,
                    token=tok,
                    bearer=args.bearer,
                    insecure=args.insecure,
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if args.cmd == "upnp-set":
        loc = resolve_location_id(args, None, tok)

        enabled = None
        if getattr(args, "enabled", None) is not None:
            enabled = args.enabled.lower() in ("true", "1")

        print(
            json.dumps(
                upnp_set(
                    args.base,
                    args.customer_id,
                    loc,
                    enabled=enabled,
                    mode=getattr(args, "mode", None),
                    token=tok,
                    bearer=args.bearer,
                    insecure=args.insecure,
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if args.cmd == "upnp-enable":
        loc = resolve_location_id(args, None, tok)
        print(
            json.dumps(
                upnp_set(
                    args.base,
                    args.customer_id,
                    loc,
                    mode="enable",
                    token=tok,
                    bearer=args.bearer,
                    insecure=args.insecure,
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if args.cmd == "upnp-disable":
        loc = resolve_location_id(args, None, tok)
        print(
            json.dumps(
                upnp_set(
                    args.base,
                    args.customer_id,
                    loc,
                    mode="disable",
                    token=tok,
                    bearer=args.bearer,
                    insecure=args.insecure,
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if args.cmd == "upnp-auto":
        loc = resolve_location_id(args, None, tok)
        print(
            json.dumps(
                upnp_set(
                    args.base,
                    args.customer_id,
                    loc,
                    mode="auto",
                    token=tok,
                    bearer=args.bearer,
                    insecure=args.insecure,
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if args.cmd == "lte-status":
        loc = resolve_location_id(args, None, tok)
        print(
            json.dumps(
                lte_status(
                    args.base,
                    loc,
                    token=tok,
                    bearer=args.bearer,
                    insecure=args.insecure,
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if args.cmd == "lte-enable":
        loc = resolve_location_id(args, None, tok)
        print(
            json.dumps(
                lte_enable(
                    args.base,
                    loc,
                    token=tok,
                    bearer=args.bearer,
                    insecure=args.insecure,
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if args.cmd == "lte-disable":
        loc = resolve_location_id(args, None, tok)
        print(
            json.dumps(
                lte_disable(
                    args.base,
                    loc,
                    token=tok,
                    bearer=args.bearer,
                    insecure=args.insecure,
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if args.cmd == "speedtest-run":
        nid = resolve_node_id(args)
        loc = resolve_location_id(args, nid, tok)
        print(
            json.dumps(
                speedtest_run(
                    args.base,
                    args.customer_id,
                    loc,
                    nid,
                    token=tok,
                    bearer=args.bearer,
                    insecure=args.insecure,
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if args.cmd == "speedtest-results":
        nid = resolve_node_id(args)
        loc = resolve_location_id(args, nid, tok)
        print(
            json.dumps(
                speedtest_results(
                    args.base,
                    args.customer_id,
                    loc,
                    nid,
                    token=tok,
                    bearer=args.bearer,
                    insecure=args.insecure,
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if args.cmd == "speedtest-result":
        nid = resolve_node_id(args)
        loc = resolve_location_id(args, nid, tok)
        print(
            json.dumps(
                speedtest_result_by_id(
                    args.base,
                    args.customer_id,
                    loc,
                    nid,
                    args.request_id,
                    token=tok,
                    bearer=args.bearer,
                    insecure=args.insecure,
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if args.cmd == "reboot":
        nid = resolve_node_id(args)
        loc = resolve_location_id(args, nid, tok)
        print(
            json.dumps(
                reboot_node(
                    args.base,
                    args.customer_id,
                    loc,
                    nid,
                    token=tok,
                    bearer=args.bearer,
                    insecure=args.insecure,
                    delay=getattr(args, "delay", None),
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if args.cmd == "get-location":
        nid = resolve_node_id(args)
        print(resolve_location_id(args, nid, tok))
        return

    if args.cmd == "dhcp-resv-list":
        nid = getattr(args, "node_id", None)
        if nid is None and getattr(args, "location_id", None) is None:
            # allow auto via serial only when location-id is omitted
            nid = resolve_node_id(args)
        loc = resolve_location_id(args, nid, tok)
        j = dhcp_resv_list(
            args.base,
            args.customer_id,
            loc,
            token=tok,
            bearer=args.bearer,
            insecure=args.insecure,
            retry_412=getattr(args, "retry_412", 0),
            retry_wait=getattr(args, "retry_wait", 10.0),
        )
        print(json.dumps(j, indent=2, ensure_ascii=False))
        return

    if args.cmd == "dhcp-resv-get":
        nid = getattr(args, "node_id", None)
        if nid is None and getattr(args, "location_id", None) is None:
            nid = resolve_node_id(args)
        loc = resolve_location_id(args, nid, tok)
        j = dhcp_resv_get(
            args.base,
            args.customer_id,
            loc,
            args.mac,
            token=tok,
            bearer=args.bearer,
            insecure=args.insecure,
            retry_412=getattr(args, "retry_412", 0),
            retry_wait=getattr(args, "retry_wait", 10.0),
        )
        print(json.dumps(j, indent=2, ensure_ascii=False))
        return

    if args.cmd == "dhcp-resv-set":
        nid = getattr(args, "node_id", None)
        if nid is None and getattr(args, "location_id", None) is None:
            nid = resolve_node_id(args)
        loc = resolve_location_id(args, nid, tok)
        j = dhcp_resv_set(
            args.base,
            args.customer_id,
            loc,
            args.mac,
            args.ip,
            getattr(args, "host_name", None),
            token=tok,
            bearer=args.bearer,
            insecure=args.insecure,
            retry_412=getattr(args, "retry_412", 0),
            retry_wait=getattr(args, "retry_wait", 10.0),
        )
        print(json.dumps(j, indent=2, ensure_ascii=False))
        return

    if args.cmd == "dhcp-resv-del":
        nid = getattr(args, "node_id", None)
        if nid is None and getattr(args, "location_id", None) is None:
            nid = resolve_node_id(args)
        loc = resolve_location_id(args, nid, tok)
        j = dhcp_resv_del(
            args.base,
            args.customer_id,
            loc,
            args.mac,
            token=tok,
            bearer=args.bearer,
            insecure=args.insecure,
            retry_412=getattr(args, "retry_412", 0),
            retry_wait=getattr(args, "retry_wait", 10.0),
        )
        print(json.dumps(j, indent=2, ensure_ascii=False))
        return

    
    if args.cmd == "factory-reset":
        # 1. 先決定 location-id（可以直接給，或透過 node-id / serial 自動解析）
        #    這裡沿用 wifi-* 指令的寫法：沒給 location-id 就用 node-id → get-location API
        loc = resolve_location_id(args, getattr(args, "node_id", None), tok)

        # 2. 組合 options
        #    - --empty → {}
        #    - 有個別欄位 → 只帶那些欄位
        #    - 都沒指定 & 非 --empty → 視為全選（options=None，由 factory_reset() 幫你全 True）
        flag_map = {
            "persons": "persons",
            "onboarding_checkpoints": "onboardingCheckpoints",
            "devices": "devices",
            "network_configuration": "networkConfiguration",
            "wifi_network": "wifiNetwork",
            "secondary_networks": "secondaryNetworks",
            "device_freeze": "deviceFreeze",
            "device_nicknames": "deviceNicknames",
            "managers": "managers",
            "wan_configuration": "wanConfiguration",
        }

        if getattr(args, "empty", False):
            # 不能跟其它選項混用，避免語意混亂
            if getattr(args, "all", False) or any(
                getattr(args, k, False) for k in flag_map.keys()
            ):
                raise SystemExit("--empty 不能與 --all 或個別欄位選項同時使用")
            options: Optional[dict] = {}
        else:
            selected: dict = {}
            for cli_opt, api_key in flag_map.items():
                if getattr(args, cli_opt, False):
                    selected[api_key] = True

            if selected:
                options = selected
            else:
                # 沒有任何欄位 → 視為 full reset（all true）
                # 不論有沒有顯式加 --all，行為都一樣
                options = None

        # 3. 呼叫 API 並印出結果
        print(
            json.dumps(
                factory_reset(
                    args.base,
                    args.customer_id,
                    loc,
                    token=tok,
                    bearer=args.bearer,
                    insecure=args.insecure,
                    options=options,
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        return
    

if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as e:  # pragma: no cover - simple CLI error handler
        r = e.response
        print(
            f"HTTP {getattr(r, 'status_code', '??')} {getattr(r, 'reason', '')}",
            file=sys.stderr,
        )
        try:
            print(json.dumps(r.json(), indent=2, ensure_ascii=False), file=sys.stderr)
        except Exception:
            print(r.text, file=sys.stderr)
        sys.exit(10)
    except Exception as e:  # pragma: no cover - simple CLI error handler
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

