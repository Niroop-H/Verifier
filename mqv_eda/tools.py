from __future__ import annotations
import shutil
import subprocess
from dataclasses import dataclass

@dataclass(frozen=True)
class ToolSpec:
    key: str
    executable: str
    version_args: tuple[str, ...]
    purpose: str
    tier: str = "optional"

TOOL_SPECS = (
    ToolSpec("iverilog", "iverilog", ("-V",), "Verilog/SystemVerilog compilation", "core"),
    ToolSpec("vvp", "vvp", ("-V",), "Icarus simulation runtime", "core"),
    ToolSpec("verilator", "verilator", ("--version",), "RTL lint and compiled simulation", "core"),
    ToolSpec("yosys", "yosys", ("-V",), "RTL synthesis and structural checks", "core"),
    ToolSpec("ghdl", "ghdl", ("--version",), "VHDL analysis and simulation", "conditional"),
    ToolSpec("sby", "sby", ("--help",), "Formal verification task runner", "conditional"),
    ToolSpec("z3", "z3", ("--version",), "SMT solver", "conditional"),
    ToolSpec("boolector", "boolector", ("--version",), "SMT solver", "optional"),
    ToolSpec("klayout", "klayout", ("-v",), "Layout and rule-deck execution", "conditional"),
    ToolSpec("opensta", "sta", ("-version",), "Static timing analysis", "conditional"),
)

def probe_tool(spec: ToolSpec, timeout: float = 8.0) -> dict:
    path = shutil.which(spec.executable)
    if not path:
        return {"state": "BLOCKED", "executable": spec.executable, "path": None,
                "purpose": spec.purpose, "tier": spec.tier}
    try:
        proc = subprocess.run([path, *spec.version_args], stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, text=True, timeout=timeout, check=False)
        lines = (proc.stdout or "").strip().splitlines()
        return {"state": "AVAILABLE", "executable": spec.executable, "path": path,
                "purpose": spec.purpose, "tier": spec.tier, "version_exit_code": proc.returncode,
                "version": " | ".join(lines[:3])[:600]}
    except subprocess.TimeoutExpired:
        return {"state": "ERROR", "executable": spec.executable, "path": path,
                "purpose": spec.purpose, "tier": spec.tier, "error": "version probe timed out"}
    except OSError as exc:
        return {"state": "ERROR", "executable": spec.executable, "path": path,
                "purpose": spec.purpose, "tier": spec.tier, "error": str(exc)}

def discover_tools() -> dict:
    import platform, sys
    return {"platform": platform.platform(), "python": sys.version.split()[0],
            "tools": {spec.key: probe_tool(spec) for spec in TOOL_SPECS}}
