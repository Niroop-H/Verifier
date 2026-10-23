#!/usr/bin/env python3
"""Non-mutating tool discovery; can run directly from a source checkout."""
from __future__ import annotations
import json, shutil, subprocess, sys, platform
from pathlib import Path

# Running scripts/check_environment.py sets sys.path[0] to scripts/, so make
# the repository root importable without requiring package installation.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mqv_eda.tools import TOOL_SPECS, probe_tool

def main() -> int:
    report = {"platform": platform.platform(), "python": sys.version.split()[0], "tools": {}}
    for spec in TOOL_SPECS:
        result = probe_tool(spec)
        report["tools"][spec.key] = {**result, "command": [spec.executable, *spec.version_args]}
    print(json.dumps(report, indent=2))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
