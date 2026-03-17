#!/usr/bin/env python3
"""
cpe_brwan_capture.py

透過 SSH 登入 CPE，在指定介面上用 tcpdump 抓一小段封包，
把 pcap 存在 controlpc 本地，最後輸出一行 JSON 結果。

使用範例：

    python3 cpe_brwan_capture.py \
        --host 192.168.1.1 \
        --user operator \
        --password 123456789 \
        --iface br-wan \
        --duration 20 \
        --filter "port 67 or port 68" \
        --output /tmp/t445252_dhcp.pcap
"""

import argparse
import json
import sys
import time
from typing import Optional

try:
    import paramiko  # type: ignore
except ImportError:
    paramiko = None


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Capture packets on CPE br-wan (or other iface) via SSH and save as pcap."
    )
    p.add_argument("--host", required=True, help="CPE IP / hostname")
    p.add_argument("--user", required=True, help="SSH username")
    p.add_argument("--password", required=True, help="SSH password")

    p.add_argument(
        "--iface",
        default="br-wan",
        help="Interface to capture on (default: br-wan)",
    )
    p.add_argument(
        "--duration",
        type=int,
        default=20,
        help="Capture duration in seconds (default: 20)",
    )
    p.add_argument(
        "--output",
        default="brwan_capture.pcap",
        help="Local output pcap filename (default: brwan_capture.pcap)",
    )
    p.add_argument(
        "--filter",
        default="",
        help="Optional tcpdump BPF filter, e.g. 'port 67 or port 68'",
    )
    p.add_argument(
        "--snaplen",
        type=int,
        default=0,
        help="Snaplen for tcpdump -s (0 = full packets, default: 0)",
    )
    p.add_argument(
        "--tcpdump-path",
        default="tcpdump",
        help="Path of tcpdump on CPE (default: tcpdump, use full path if needed)",
    )

    return p.parse_args()


def build_tcpdump_cmd(
    iface: str, snaplen: int, bpf_filter: str, tcpdump_path: str
) -> str:
    # -U: packet-buffered, -n: no DNS, -q: less verbose, -w -: write pcap to stdout
    s_opt = snaplen if snaplen > 0 else 0
    base = f"{tcpdump_path} -i {iface} -s {s_opt} -U -n -q -w -"
    if bpf_filter:
        base += f" {bpf_filter}"
    return base


def ssh_connect(host: str, user: str, password: str) -> "paramiko.SSHClient":
    if paramiko is None:
        raise RuntimeError(
            "paramiko is not installed. Please `pip install paramiko` "
            "and在 tools 的 requirements.txt 加上 `paramiko>=3.0.0`。"
        )

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        host,
        username=user,
        password=password,
        timeout=10,
        look_for_keys=False,
        allow_agent=False,
    )
    return client


def do_capture(args: argparse.Namespace) -> int:
    start_ts = time.time()

    try:
        client = ssh_connect(args.host, args.user, args.password)
    except Exception as e:
        print_json(
            ok=False,
            mode="capture",
            host=args.host,
            error=f"ssh_connect_failed: {e}",
            stage="ssh_connect",
        )
        return 1

    cmd = build_tcpdump_cmd(args.iface, args.snaplen, args.filter, args.tcpdump_path)

    try:
        transport = client.get_transport()
        if transport is None:
            raise RuntimeError("no SSH transport")
        chan = transport.open_session()
        # 不要 request_pty()，避免破壞 binary pcap
        chan.exec_command(cmd)
    except Exception as e:
        print_json(
            ok=False,
            mode="capture",
            host=args.host,
            error=f"ssh_exec_failed: {e}",
            stage="ssh_exec",
            cmd=cmd,
        )
        client.close()
        return 1

    bytes_written = 0
    deadline = start_ts + max(1, int(args.duration))

    try:
        with open(args.output, "wb") as f:
            while True:
                now = time.time()
                if now >= deadline:
                    # 超過時間就關閉 channel，tcpdump 會被斷線終止
                    chan.close()
                    break

                if chan.recv_ready():
                    chunk = chan.recv(4096)
                    if not chunk:
                        # remote side closed
                        break
                    f.write(chunk)
                    bytes_written += len(chunk)
                else:
                    # 微睡，降低 busy loop
                    time.sleep(0.05)
    finally:
        try:
            chan.close()
        except Exception:
            pass
        client.close()

    duration_real = int(time.time() - start_ts)

    print_json(
        ok=True,
        mode="capture",
        host=args.host,
        iface=args.iface,
        duration_sec=duration_real,
        output=args.output,
        bytes=bytes_written,
        filter=args.filter,
        snaplen=args.snaplen,
    )
    return 0


def print_json(**data: Optional[object]) -> None:
    # 確保只輸出一行 JSON，給 caller 好 parse
    sys.stdout.write(json.dumps(data, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def main() -> None:
    args = parse_args()
    try:
        rc = do_capture(args)
    except KeyboardInterrupt:
        print_json(
            ok=False,
            mode="capture",
            host=getattr(args, "host", None),
            error="keyboard_interrupt",
            stage="local",
        )
        rc = 130
    sys.exit(rc)


if __name__ == "__main__":
    main()

