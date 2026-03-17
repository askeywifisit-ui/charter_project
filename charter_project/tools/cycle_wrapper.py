#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wrapper aligned to your working style:
- Always search manifest.yaml next to this file (and fallback to CWD).
- Require PyYAML; if missing, log and exit rc=2 so runner installs deps.
- Keep ORIGINAL_ENTRY fallback and JSON events.
"""
import os, time, importlib, json, sys, traceback

try:
    import yaml
except Exception as e:
    print(json.dumps({"event":"wrapper_error","msg":"PyYAML missing","detail":str(e)}))
    sys.exit(2)

def _to_bool(s): return str(s).strip() in ("1","true","True","YES","yes","y")

def _manifest_candidates():
    here = os.path.dirname(os.path.abspath(__file__))
    return [
        os.path.join(here, "manifest.yaml"),
        os.path.join(os.getcwd(), "manifest.yaml"),
    ]

def _load_env():
    last_err = None
    for p in _manifest_candidates():
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                env = data.get("env") or {}
                applied = {}
                for k, v in env.items():
                    if k not in os.environ or os.environ.get(k) == "":
                        os.environ[k] = str(v)
                        applied[k] = os.environ[k]
                print(json.dumps({"event":"manifest_env_loaded","path":p,"count":len(applied)}, ensure_ascii=False))
                return True
            except Exception as e:
                last_err = str(e)
                print(json.dumps({"event":"manifest_env_error","path":p,"error":last_err}, ensure_ascii=False))
                break
    print(json.dumps({"event":"manifest_env_skip","reason":"file_not_found","candidates":_manifest_candidates()}, ensure_ascii=False))
    return False

def _load_target(spec: str):
    if not spec or ":" not in spec:
        raise ValueError(f"Bad ORIGINAL_ENTRY '{spec}' (expected 'module:func' or 'file.py:func')")
    mod_path, func_name = spec.split(":", 1)
    if mod_path.endswith(".py"):
        mod_path = mod_path[:-3]
    mod = importlib.import_module(mod_path)
    if not hasattr(mod, func_name):
        raise AttributeError(f"Function '{func_name}' not found in module '{mod_path}'")
    return getattr(mod, func_name)

def run() -> int:
    _load_env()

    name = os.environ.get("SCRIPT_NAME") or os.environ.get("name") or "C4123492_GetToken_NodeID_likeWAN"
    cycles = int(os.environ.get("CYCLES","1"))
    interval = float(os.environ.get("CYCLE_INTERVAL","0.5"))
    stop_on_fail = _to_bool(os.environ.get("STOP_ON_FAIL","1"))

    target_spec = os.environ.get("ORIGINAL_ENTRY") or "main_impl.py:run"
    if target_spec.endswith(".py:run"):
        target_spec = target_spec.replace(".py:",":")

    try:
        target = _load_target(target_spec)
        print(json.dumps({"event":"entry_use","target_spec":target_spec}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"event":"entry_error","target_spec":target_spec,"error":str(e)}, ensure_ascii=False))
        return 2

    print(json.dumps({"event":"runner_start","name":name,"cycles":cycles}, ensure_ascii=False))

    total, passed, failures = cycles, 0, []
    for i in range(1, cycles+1):
        t0 = time.time()
        rc = 1
        try:
            rc = int(target())
        except SystemExit as e:
            rc = int(e.code or 0)
        except Exception as e:
            print(json.dumps({"event":"cycle_exception","cycle":i,"error":str(e),"trace":traceback.format_exc()}, ensure_ascii=False))
            rc = 1

        if rc == 0:
            passed += 1
            print(json.dumps({"event":"cycle_pass","cycle":i}, ensure_ascii=False))
        else:
            failures.append({"cycle":i,"rc":rc})
            print(json.dumps({"event":"cycle_fail","cycle":i,"rc":rc}, ensure_ascii=False))
            if stop_on_fail:
                break

        if i < cycles:
            time.sleep(interval)

    failed = total - passed
    print(json.dumps({"event":"runner_summary","total":total,"passed":passed,"failed":failed,"failures":failures}, ensure_ascii=False))
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(run())
