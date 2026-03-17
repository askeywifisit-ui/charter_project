#!/usr/bin/env python3
"""cpe_capture_role.py

在 control PC 透過 SSH 連入 CPE 執行 tcpdump 抓封包，並把 pcap 存回 control PC。

A) 方案（你指定的 fallback）：
- role=lan：優先 br-home → eth1 → 探測
- role=wan：優先 br-wan → eth0 → 探測

封包落點：預設輸出到當前工作目錄底下 ./artifacts/pcap/（因此在 run_XXXX/ 執行會落在 run_XXXX/ 下）

模式：
- method=stream：tcpdump -w - 直接把 pcap binary 串流回 control PC
- method=sftp：CPE 先寫到 /tmp/*.pcap，再用 SFTP 抓回 control PC

自動 fallback：若 stream 執行時遇到 "Channel closed" / ssh exec 失敗，會自動切到 sftp。

範例：
  python3 cpe_capture_role.py --host 192.168.1.1 --user operator --password 123456789 \
    --role lan --duration 20 --filter "udp port 1900"

  python3 cpe_capture_role.py --host 192.168.1.1 --user operator --password 123456789 \
    --role wan --duration 20 --filter "port 67 or port 68"

  # 強制用 sftp 模式（遇到某些 CPE 對 binary stdout 會更穩）
  python3 cpe_capture_role.py ... --method sftp

  # 若 tcpdump 需要權限：
  python3 cpe_capture_role.py ... --sudo
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from typing import Optional, Tuple, List

try:
    import paramiko
except Exception:
    paramiko = None


def jprint(**obj):
    print(json.dumps(obj, ensure_ascii=False))


# --------------------------- SSH helpers ---------------------------

def ssh_connect(host: str, user: str, password: str) -> "paramiko.SSHClient":
    if paramiko is None:
        raise RuntimeError("paramiko is not installed")

    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(
        host,
        username=user,
        password=password,
        timeout=10,
        look_for_keys=False,
        allow_agent=False,
    )
    return c


def ssh_run(client: "paramiko.SSHClient", cmd: str, timeout: int = 8, get_pty: bool = False) -> Tuple[int, str, str]:
    """Run a small command and return (rc, stdout, stderr)."""
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout, get_pty=get_pty)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    rc = stdout.channel.recv_exit_status()
    return rc, out, err


def iface_exists(client: "paramiko.SSHClient", iface: str) -> bool:
    rc, _, _ = ssh_run(client, f"ip link show dev {iface} >/dev/null 2>&1 || exit 2", timeout=6)
    return rc == 0


def list_ifaces(client: "paramiko.SSHClient") -> List[str]:
    rc, out, _ = ssh_run(client, "ls -1 /sys/class/net 2>/dev/null", timeout=6)
    if rc == 0 and out.strip():
        return [x.strip() for x in out.splitlines() if x.strip()]
    rc, out, _ = ssh_run(client, "ip -o link show 2>/dev/null | awk -F': ' '{print $2}'", timeout=6)
    if rc == 0 and out.strip():
        return [x.strip() for x in out.splitlines() if x.strip()]
    return []


def probe_default_route_dev(client: "paramiko.SSHClient") -> Optional[str]:
    cmd = "ip route show default 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i==\"dev\"){print $(i+1); exit}}'"
    rc, out, _ = ssh_run(client, cmd, timeout=6)
    if rc == 0 and out.strip():
        dev = out.strip().splitlines()[0].strip()
        return dev or None
    return None


def pick_iface_by_role(client: "paramiko.SSHClient", role: str) -> Tuple[str, str]:
    role = role.lower().strip()
    if role not in ("wan", "lan"):
        raise ValueError(f"invalid role: {role}")

    preferred = ["br-home", "eth1"] if role == "lan" else ["br-wan", "eth0"]

    for cand in preferred:
        if iface_exists(client, cand):
            return cand, f"preferred:{cand}"

    default_dev = None
    try:
        default_dev = probe_default_route_dev(client)
    except Exception:
        default_dev = None

    if role == "wan" and default_dev and iface_exists(client, default_dev):
        return default_dev, f"probe:default_route:{default_dev}"

    ifaces = list_ifaces(client)

    # LAN: prefer any bridge-like iface (br-*) except br-wan
    if role == "lan":
        for cand in ifaces:
            if cand.startswith("br-") and cand != "br-wan" and iface_exists(client, cand):
                return cand, f"probe:bridge:{cand}"

    # fallback: pick a likely ethernet-like iface (excluding lo and default_dev)
    for cand in ifaces:
        if cand in ("lo", default_dev):
            continue
        if re.match(r"^(eth\d+|en\w+|br-\w+|wlan\d+|wl\w+)$", cand) and iface_exists(client, cand):
            return cand, f"probe:any:{cand}"

    if default_dev and iface_exists(client, default_dev):
        return default_dev, f"probe:fallback_default:{default_dev}"

    raise RuntimeError(f"cannot resolve interface for role={role}; ifaces={ifaces}")


# --------------------------- capture commands ---------------------------

def _tcpdump_base(
    iface: str,
    snaplen: int,
    bpf_filter: str,
    tcpdump_path: str,
    sudo: bool,
    out_target: str,
) -> str:
    """Return tcpdump command string."""
    sudo_prefix = "sudo -n " if sudo else ""
    cmd = f"{sudo_prefix}{tcpdump_path} -i {iface}"
    if snaplen and snaplen > 0:
        cmd += f" -s {int(snaplen)}"
    cmd += " -U"
    cmd += f" -w {out_target}"
    if bpf_filter:
        cmd += f" {bpf_filter}"
    return cmd


def build_remote_wrapped_capture(cmd: str, duration: int) -> str:
    """Wrap tcpdump command to stop after duration via SIGINT (flushes pcap)."""
    d = max(1, int(duration))
    inner = f"{cmd} & pid=$!; sleep {d}; kill -2 $pid >/dev/null 2>&1; wait $pid"
    # Use sh -c '...'
    return "sh -c " + repr(inner)


def resolve_output_path(output_arg: str, role: str, iface: str) -> Tuple[str, str]:
    """Return (output_rel, output_abs). Ensure dir exists."""
    output_arg = (output_arg or "").strip()
    if output_arg:
        out = output_arg
        # If it's a directory, append auto filename
        if out.endswith("/") or (os.path.exists(out) and os.path.isdir(out)):
            ts = time.strftime("%Y%m%d_%H%M%S")
            out = os.path.join(out, f"{role}_{iface}_{ts}.pcap")
    else:
        ts = time.strftime("%Y%m%d_%H%M%S")
        outdir = os.path.join(".", "artifacts", "pcap")
        os.makedirs(outdir, exist_ok=True)
        out = os.path.join(outdir, f"{role}_{iface}_{ts}.pcap")

    out_abs = os.path.abspath(out)
    os.makedirs(os.path.dirname(out_abs) or ".", exist_ok=True)
    return out, out_abs


def diagnose_tcpdump(client: "paramiko.SSHClient", tcpdump_path: str) -> dict:
    """Best-effort diagnostics for tcpdump availability/permission."""
    diag = {}
    try:
        rc, out, err = ssh_run(client, f"command -v {tcpdump_path} 2>/dev/null || which {tcpdump_path} 2>/dev/null || true", timeout=6)
        diag["tcpdump_which"] = (out.strip() or err.strip() or "").splitlines()[:3]
    except Exception as e:
        diag["tcpdump_which"] = [f"error:{e}"]

    try:
        rc, out, err = ssh_run(client, f"{tcpdump_path} -h 2>&1 | head -n 3", timeout=6)
        diag["tcpdump_help"] = (out.strip() or err.strip() or "").splitlines()[:3]
    except Exception as e:
        diag["tcpdump_help"] = [f"error:{e}"]

    try:
        rc, out, err = ssh_run(client, "id 2>/dev/null || true", timeout=6)
        diag["id"] = (out.strip() or err.strip() or "").splitlines()[:3]
    except Exception as e:
        diag["id"] = [f"error:{e}"]

    return diag


# --------------------------- capture methods ---------------------------

def capture_stream(
    client: "paramiko.SSHClient",
    remote_cmd: str,
    output_abs: str,
    duration: int,
) -> Tuple[bool, int | None, int, str]:
    """Run remote_cmd that streams pcap to stdout. Return (ok, rc, bytes, stderr_tail)."""
    transport = client.get_transport()
    if transport is None:
        raise RuntimeError("no SSH transport")

    chan = transport.open_session()
    # IMPORTANT: do NOT request PTY for binary stream
    chan.exec_command(remote_cmd)

    bytes_written = 0
    stderr_buf = bytearray()

    local_deadline = time.time() + max(10, int(duration) + 12)

    with open(output_abs, "wb") as f:
        while True:
            if chan.recv_ready():
                chunk = chan.recv(65536)
                if not chunk:
                    break
                f.write(chunk)
                bytes_written += len(chunk)
                continue

            if chan.recv_stderr_ready():
                errc = chan.recv_stderr(4096)
                if errc:
                    stderr_buf.extend(errc)

            if chan.exit_status_ready():
                # drain
                while chan.recv_ready():
                    chunk = chan.recv(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    bytes_written += len(chunk)
                while chan.recv_stderr_ready():
                    errc = chan.recv_stderr(4096)
                    if not errc:
                        break
                    stderr_buf.extend(errc)
                break

            if time.time() >= local_deadline:
                try:
                    chan.close()
                except Exception:
                    pass
                break

            time.sleep(0.05)

    try:
        rc = chan.recv_exit_status()
    except Exception:
        rc = None
    try:
        chan.close()
    except Exception:
        pass

    stderr_tail = stderr_buf.decode("utf-8", errors="replace")[-2000:].strip()
    ok = bytes_written > 24
    return ok, rc, bytes_written, stderr_tail


def capture_sftp(
    client: "paramiko.SSHClient",
    remote_cmd: str,
    remote_pcap: str,
    output_abs: str,
    duration: int,
    get_pty: bool,
) -> Tuple[bool, int | None, int, str]:
    """Run remote_cmd that writes pcap to remote_pcap, then download via SFTP."""
    # Execute capture (no binary streaming). PTY is safe here.
    try:
        stdin, stdout, stderr = client.exec_command(remote_cmd, get_pty=get_pty)
        # wait
        rc = stdout.channel.recv_exit_status()
        err_txt = (stderr.read().decode("utf-8", errors="replace") or "").strip()
    except Exception as e:
        raise RuntimeError(f"sftp_capture_exec_failed: {e}")

    # Download
    sftp = client.open_sftp()
    bytes_written = 0
    try:
        sftp.get(remote_pcap, output_abs)
        try:
            bytes_written = os.path.getsize(output_abs)
        except Exception:
            bytes_written = 0
    finally:
        try:
            sftp.close()
        except Exception:
            pass

    # Cleanup remote file best-effort
    try:
        ssh_run(client, f"rm -f {remote_pcap} >/dev/null 2>&1 || true", timeout=6)
    except Exception:
        pass

    ok = bytes_written > 24
    return ok, rc, bytes_written, err_txt[-2000:]


# --------------------------- main flow ---------------------------

def do_capture(args: argparse.Namespace) -> int:
    t0 = time.time()

    try:
        client = ssh_connect(args.host, args.user, args.password)
    except Exception as e:
        jprint(ok=False, mode="capture", host=args.host, stage="ssh_connect", error=f"ssh_connect_failed: {e}")
        return 1

    # Resolve iface
    try:
        if args.iface:
            iface = args.iface
            if not iface_exists(client, iface):
                raise RuntimeError(f"iface_not_found:{iface}")
            iface_how = "cli:iface"
        else:
            iface, iface_how = pick_iface_by_role(client, args.role)
    except Exception as e:
        diag = {}
        try:
            diag = {"ifaces": list_ifaces(client)}
        except Exception:
            pass
        jprint(
            ok=False,
            mode="capture",
            host=args.host,
            stage="iface",
            error=f"iface_resolve_failed: {e}",
            role=args.role,
            iface=args.iface,
            **diag,
        )
        client.close()
        return 1

    output_rel, output_abs = resolve_output_path(args.output, args.role, iface)

    # Build remote commands
    duration = int(args.duration)

    # STREAM remote cmd (stdout pcap)
    stream_tcpdump = _tcpdump_base(
        iface=iface,
        snaplen=args.snaplen,
        bpf_filter=args.filter,
        tcpdump_path=args.tcpdump_path,
        sudo=args.sudo,
        out_target="-",
    )
    stream_cmd = build_remote_wrapped_capture(stream_tcpdump, duration)

    # SFTP remote cmd (remote file)
    remote_dir = (args.remote_dir or "/tmp").rstrip("/")
    ts = time.strftime("%Y%m%d_%H%M%S")
    remote_pcap = f"{remote_dir}/cap_{args.role}_{iface}_{ts}_{os.getpid()}.pcap"
    sftp_tcpdump = _tcpdump_base(
        iface=iface,
        snaplen=args.snaplen,
        bpf_filter=args.filter,
        tcpdump_path=args.tcpdump_path,
        sudo=args.sudo,
        out_target=remote_pcap,
    )
    sftp_cmd = build_remote_wrapped_capture(sftp_tcpdump, duration)

    method = args.method
    bytes_written = 0
    rc = None
    stderr_tail = ""
    used_method = method

    try:
        if method == "stream":
            try:
                ok, rc, bytes_written, stderr_tail = capture_stream(client, stream_cmd, output_abs, duration)
                used_method = "stream"
                if not ok:
                    # fall back if file too small (tcpdump failed)
                    raise RuntimeError("stream_no_pcap")
            except Exception as e:
                # if channel closed / exec failed etc -> fallback to sftp
                ok, rc, bytes_written, stderr_tail = capture_sftp(
                    client,
                    sftp_cmd,
                    remote_pcap,
                    output_abs,
                    duration,
                    get_pty=bool(args.sudo_pty),
                )
                used_method = f"sftp(fallback:{type(e).__name__})"
        else:
            ok, rc, bytes_written, stderr_tail = capture_sftp(
                client,
                sftp_cmd,
                remote_pcap,
                output_abs,
                duration,
                get_pty=bool(args.sudo_pty),
            )
            used_method = "sftp"

    except Exception as e:
        diag = diagnose_tcpdump(client, args.tcpdump_path)
        client.close()
        jprint(
            ok=False,
            mode="capture",
            host=args.host,
            stage="capture",
            role=args.role,
            iface=iface,
            iface_how=iface_how,
            method=used_method,
            error=str(e),
            cmd_stream=stream_cmd,
            cmd_sftp=sftp_cmd,
            remote_pcap=remote_pcap,
            output=output_rel,
            output_abs=output_abs,
            **diag,
        )
        return 2

    client.close()

    sec = round(time.time() - t0, 3)
    ok_final = bool(bytes_written > 24)

    jprint(
        ok=ok_final,
        mode="capture",
        host=args.host,
        role=args.role,
        iface=iface,
        iface_how=iface_how,
        method=used_method,
        duration=duration,
        sec=sec,
        bytes=bytes_written,
        rc=rc,
        output=output_rel,
        output_abs=output_abs,
        stderr=stderr_tail,
        cmd=(stream_cmd if "stream" in used_method else sftp_cmd),
        remote_pcap=(remote_pcap if "sftp" in used_method else ""),
    )

    return 0 if ok_final else 2


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Capture pcap from CPE via SSH (WAN/LAN role aware)")
    p.add_argument("--host", required=True)
    p.add_argument("--user", required=True)
    p.add_argument("--password", required=True)

    p.add_argument("--role", choices=["wan", "lan"], default="wan")
    p.add_argument("--iface", default=None, help="Override interface directly")

    p.add_argument("--duration", type=int, default=20)
    p.add_argument("--filter", default="", help="tcpdump BPF filter")
    p.add_argument("--snaplen", type=int, default=0)
    p.add_argument("--tcpdump-path", dest="tcpdump_path", default="tcpdump")

    p.add_argument("--output", default="", help="Local output path. Default: ./artifacts/pcap/<auto>.pcap")

    p.add_argument(
        "--method",
        choices=["stream", "sftp"],
        default="stream",
        help="stream=stdout pcap; sftp=remote file then download. stream will auto fallback to sftp on exec/channel errors.",
    )

    p.add_argument(
        "--remote-dir",
        default="/tmp",
        help="Remote directory for sftp method (default: /tmp)",
    )

    p.add_argument(
        "--sudo",
        action="store_true",
        help="Run tcpdump via sudo -n (no password prompt)",
    )

    p.add_argument(
        "--sudo-pty",
        action="store_true",
        help="When using sftp method, allocate PTY for the capture command (useful if sudo requires a tty).",
    )

    return p


def main() -> None:
    args = build_parser().parse_args()
    try:
        rc = do_capture(args)
    except KeyboardInterrupt:
        jprint(ok=False, mode="capture", host=getattr(args, "host", None), stage="local", error="keyboard_interrupt")
        rc = 130
    sys.exit(rc)


if __name__ == "__main__":
    main()
