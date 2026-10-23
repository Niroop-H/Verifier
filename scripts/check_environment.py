#!/usr/bin/env python3
"""Non-mutating discovery of EDA tools; missing tools are reported, never faked."""
from __future__ import annotations
import json, os, shutil, subprocess, sys
from pathlib import Path

TOOLS = {
    "iverilog": ["iverilog", "-V"],
    "vvp": ["vvp", "-V"],
    "verilator": ["verilator", "--version"],
    "yosys": ["yosys", "-V"],
    "ghdl": ["ghdl", "--version"],
    "sby": ["sby", "--version"],
    "z3": ["z3", "--version"],
    "boolector": ["boolector", "--version"],
    "klayout": ["klayout", "-v"],
    "opensta": ["sta", "-version"],
}
def main() -> int:
    report = {"platform": sys.platform, "python": sys.version.split()[0], "tools": {}}
    for name, cmd in TOOLS.items():
        path = shutil.which(cmd[0])
        item = {"state": "AVAILABLE" if path else "BLOCKED", "path": path, "command": cmd}
        if path:
            try:
                p = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=8)
                item["exit_code"] = p.returncode
                item["version_output"] = p.stdout[:1500]
            except Exception as exc:
                item["state"] = "ERROR"
                item["error"] = f"{type(exc).__name__}: {exc}"
        report["tools"][name] = item
    print(json.dumps(report, indent=2))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
