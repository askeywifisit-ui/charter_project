#!/usr/bin/env python3
"""
collect_cpe_logs.py — shared "fail → pull CPE logs" helper (v2)

Changes from v1:
- --force / CPE_LOG_FORCE=1 to ignore .pulled sentinel and pull again.
- CPE_LOG_MULTI=1 to allow multiple pulls (sentinel disabled).
- Structured JSON logs for GUI (unchanged).

Extra:
- SSH 連線前先做 TCP port 掃描；若 SSH port 未開，會記錄 event 並視為 LAN pull 失敗。
"""

import os, sys, json, subprocess, pathlib, glob, time, socket

# --- fallback for SSH creds (inserted) ---
try:
    _ENV_SSH_USER = os.environ.get("SSH_USER") or os.environ.get("CPE_USER")
    _ENV_SSH_PWD  = os.environ.get("SSH_PASSWORD") or os.environ.get("CPE_PASSWORD")
except Exception:
    _ENV_SSH_USER = None
    _ENV_SSH_PWD = None
# --- end fallback ---


def now_ts():
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


def jlog(event: str, **kw):
    rec = {"event": event, "ts": now_ts(), **kw}
    print(json.dumps(rec, ensure_ascii=False), flush=True)


def run_cmd(cmd, timeout=None):
    jlog("proc_start", cmd=cmd, timeout=timeout)
    try:
        p = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
        jlog(
            "proc_end",
            rc=p.returncode,
            out=p.stdout[-800:],
            err=p.stderr[-800:],
        )
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        jlog("proc_timeout", cmd=cmd)
        return 124, "", "timeout"


def is_ssh_open(host: str, port: int = 22, timeout: float = 3.0) -> bool:
    """
    簡單測試 TCP host:port 是否可連線。
    成功回 True，失敗回 False。
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        return True
    except OSError:
        return False
    finally:
        try:
            s.close()
        except Exception:
            pass


def enable_cloud_ssh_if_needed():
    if os.environ.get("USE_CLOUD_SSH", "0") != "1":
        return False, "skip"
    base = os.environ.get("NOC_BASE", "")
    email = os.environ.get("NOC_EMAIL", "")
    pwd = os.environ.get("NOC_PASSWORD", "")
    if not (base and email and pwd):
        return False, "noc_env_missing"
    cli = pathlib.Path("noc_api_cli.py")
    if not cli.exists():
        cli = pathlib.Path("/home/da40/charter/tools/noc_api_cli.py")
    if cli.exists():
        jlog("cloud_ssh_enable_try", via=str(cli), base=base)
        rc1, out1, err1 = run_cmd(
            ["python3", str(cli), "login", "--base", base, "--email", email, "--password", pwd],
            timeout=30,
        )
        rc2, out2, err2 = run_cmd(
            ["python3", str(cli), "ssh-enable", "--base", base, "--email", email, "--password", pwd],
            timeout=60,
        )
        ok = (rc1 == 0 and rc2 == 0)
        jlog(
            "cloud_ssh_enable_result",
            ok=ok,
            rc_login=rc1,
            rc_enable=rc2,
        )
        return ok, (err1 + err2)[-200:]
    else:
        jlog("cloud_ssh_enable_skip", reason="noc_api_cli_not_found")
        return False, "cli_missing"


def file_meta(path):
    try:
        st = os.stat(path)
        return {
            "name": os.path.basename(path),
            "size": st.st_size,
            "mtime": st.st_mtime,
        }
    except FileNotFoundError:
        return None


def write_index_json(dest_dir):
    items = []
    for p in glob.glob(os.path.join(dest_dir, "*.tar.gz")):
        m = file_meta(p)
        if m:
            items.append(m)
    items.sort(key=lambda x: x["mtime"], reverse=True)
    idx = {"generated_at": now_ts(), "archives": items}
    pathlib.Path(os.path.join(dest_dir, "index.json")).write_text(
        json.dumps(idx, ensure_ascii=False, indent=2)
    )


def parse_args(argv):
    # very light parser: collect run_id + reason + optional --force
    run_id = None
    reason = "failure"
    force = False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("-f", "--force"):
            force = True
            i += 1
        elif run_id is None:
            try:
                run_id = int(a)
            except ValueError:
                pass
            i += 1
        else:
            reason = a
            i += 1
    if os.environ.get("CPE_LOG_FORCE", "0") == "1":
        force = True
    return run_id, reason, force


def main():
    if len(sys.argv) < 2:
        print("usage: collect_cpe_logs.py <run_id> [reason] [--force]", file=sys.stderr)
        return 2

    run_id, reason, force = parse_args(sys.argv[1:])
    if run_id is None:
        print("usage: collect_cpe_logs.py <run_id> [reason] [--force]", file=sys.stderr)
        return 2

    WORK_BASE = os.environ.get("WORK_BASE", "/home/da40/charter/data/work")
    run_dir = os.path.join(WORK_BASE, f"run_{run_id}")
    dest_dir = os.path.join(run_dir, "cpe_log")
    pathlib.Path(dest_dir).mkdir(parents=True, exist_ok=True)

    multi = os.environ.get("CPE_LOG_MULTI", "0") == "1"

    # lock + sentinel (avoid concurrent pulls / duplicates)
    lock_path = os.path.join(dest_dir, ".pull.lock")
    sentinel = os.path.join(dest_dir, ".pulled")

    # lock: still protect concurrent pulls even in multi mode
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
    except FileExistsError:
        jlog("logpull_skip", run_id=run_id, reason="locked", dest=dest_dir)
        return 0

    try:
        if (not force) and (not multi) and os.path.exists(sentinel):
            jlog("logpull_skip", run_id=run_id, reason="already_pulled", dest=dest_dir)
            write_index_json(dest_dir)
            return 0

        jlog(
            "logpull_start",
            run_id=run_id,
            reason=reason,
            dest=dest_dir,
            force=force,
            multi=multi,
        )

        # envs
        CPE_SSH_TOOL = os.environ.get("CPE_SSH_TOOL", "/home/da40/charter/tools/cpe_ssh.py")
        host = os.environ.get("SSH_HOST_LAN", "192.168.1.1")
        user = os.environ.get("SSH_USER", "operator")
        pwd = os.environ.get("SSH_PASSWORD", "")
        latest_dir = os.environ.get("CPE_LOG_DIR_REMOTE", "/tmp/logpull")
        pattern = os.environ.get("CPE_LOG_PATTERN", "*.tar.gz")
        timeout_sec = int(os.environ.get("CPE_LOG_TIMEOUT_SEC", "180"))
        pre = os.environ.get("CPE_LOG_PRE_RUN", "1") == "1"
        rename = os.environ.get("CPE_LOG_RENAME_WITH_NODE_ID", "1") == "1"
        drem = os.environ.get("CPE_LOG_DELETE_REMOTE", "0") == "1"

        # SSH port：預設 22，可用 SSH_PORT 覆蓋
        ssh_port = int(os.environ.get("SSH_PORT", "22"))

        before = set(glob.glob(os.path.join(dest_dir, "*.tar.gz")))

        # Build command
        cmd = [
            "python3",
            CPE_SSH_TOOL,
            "--host",
            host,
            "--user",
            user,
            "--password",
            pwd,
            "--cmd",
            "pull-log",
            "--latest-from-dir",
            latest_dir,
            "--pattern",
            pattern,
            "--dest",
            dest_dir,
        ]
        if pre:
            cmd += ["--pre-logpull", "--logpull-timeout", "120"]
        if rename:
            cmd += ["--rename-with-node-id"]
        if drem:
            cmd += ["--delete-remote"]

        # Try LAN first：先做 SSH port 掃描
        if not is_ssh_open(host, ssh_port, timeout=3.0):
            # 不直接把整個 fail-hook 當錯誤，只是當作「LAN pull 失敗」
            jlog(
                "logpull_ssh_port_closed",
                host=host,
                port=ssh_port,
                note="skip_lan_pull_log",
            )
            rc, out, err = 255, "", f"ssh port {ssh_port} closed"
        else:
            rc, out, err = run_cmd(cmd, timeout=timeout_sec)
        ok = rc == 0

        # If failed, try enable cloud ssh then retry once
        if not ok and os.environ.get("USE_CLOUD_SSH", "0") == "1":
            eok, _ = enable_cloud_ssh_if_needed()
            if eok:
                time.sleep(3)
                rc, out, err = run_cmd(cmd, timeout=timeout_sec)
                ok = rc == 0

        # Detect newly created archive
        created = None
        try:
            after = set(glob.glob(os.path.join(dest_dir, "*.tar.gz")))
            added = sorted(
                after - before,
                key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0,
                reverse=True,
            )
            if added:
                created = added[0]
            else:
                cands = glob.glob(os.path.join(dest_dir, "*.tar.gz"))
                if cands:
                    created = max(cands, key=os.path.getmtime)
        except Exception as e:
            jlog("scan_error", error=str(e))

        meta = None
        if created:
            st = os.stat(created)
            meta = {
                "name": os.path.basename(created),
                "size": st.st_size,
                "mtime": st.st_mtime,
            }

        write_index_json(dest_dir)
        jlog("logpull_result", ok=ok, rc=rc, created=meta, dest=dest_dir)

        # sentinel only when not multi mode (multi mode允許反覆抓)
        if ok and (not multi):
            pathlib.Path(sentinel).write_text(now_ts())

        ret_nonzero = os.environ.get("RETURN_NONZERO_ON_FAIL", "0") == "1"
        return 0 if not ret_nonzero else (0 if ok else 1)

    finally:
        try:
            os.remove(lock_path)
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    raise SystemExit(main())

