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
    integration_level: str = "RUNTIME_DISCOVERY"

TOOL_SPECS = (
    ToolSpec("iverilog", "iverilog", ("-V",), "Verilog/SystemVerilog compilation", "core", "EXECUTION_ADAPTER"),
    ToolSpec("vvp", "vvp", ("-V",), "Icarus simulation runtime", "core", "EXECUTION_ADAPTER"),
    ToolSpec("verilator", "verilator", ("--version",), "RTL lint and compiled simulation", "core", "EXECUTION_ADAPTER"),
    ToolSpec("yosys", "yosys", ("-V",), "RTL synthesis and structural checks", "core", "EXECUTION_ADAPTER"),
    ToolSpec("ghdl", "ghdl", ("--version",), "VHDL analysis and simulation", "conditional", "EXECUTION_ADAPTER"),
    ToolSpec("sby", "sby", ("--help",), "Formal verification task runner", "conditional", "EXECUTION_ADAPTER"),
    ToolSpec("z3", "z3", ("--version",), "SMT solver", "conditional", "SOLVER_ADAPTER"),
    ToolSpec("boolector", "boolector", ("--version",), "SMT solver", "optional", "SOLVER_DISCOVERY"),
    ToolSpec("klayout", "klayout", ("-v",), "Layout and rule-deck execution", "conditional", "EXECUTION_ADAPTER"),
    ToolSpec("opensta", "sta", ("-version",), "Static timing analysis", "conditional", "EXECUTION_ADAPTER"),
    ToolSpec("openroad", "openroad", ("-version",), "Physical design flow engine"),
    ToolSpec("verible", "verible-verilog-lint", ("--version",), "SystemVerilog lint"),
    ToolSpec("surelog", "surelog", ("--version",), "SystemVerilog parsing/elaboration"),
    ToolSpec("slang", "slang", ("--version",), "SystemVerilog semantic analysis"),
    ToolSpec("sv2v", "sv2v", ("--version",), "SystemVerilog-to-Verilog conversion"),
    ToolSpec("eqy", "eqy", ("--help",), "Hardware equivalence checking"),
    ToolSpec("ngspice", "ngspice", ("--version",), "SPICE simulation"),
    ToolSpec("nvc", "nvc", ("--version",), "VHDL simulator"),
    ToolSpec("cocotb", "cocotb-config", ("--version",), "Python HDL testbench framework"),
    ToolSpec("fusesoc", "fusesoc", ("--version",), "HDL project/build orchestration"),
    ToolSpec("openlane", "openlane", ("--version",), "RTL-to-GDS flow orchestration"),
    ToolSpec("librelane", "librelane", ("--version",), "RTL-to-GDS flow orchestration"),
)

def probe_tool(spec: ToolSpec, timeout: float = 8.0) -> dict:
    path = shutil.which(spec.executable)
    base = {"executable": spec.executable, "path": path, "purpose": spec.purpose,
            "tier": spec.tier, "integration_level": spec.integration_level}
    if not path:
        return {"state": "BLOCKED", **base}
    try:
        proc = subprocess.run([path, *spec.version_args], stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, text=True, timeout=timeout, check=False)
        lines = (proc.stdout or "").strip().splitlines()
        return {"state": "AVAILABLE", **base, "version_exit_code": proc.returncode,
                "version": " | ".join(lines[:3])[:600]}
    except subprocess.TimeoutExpired:
        return {"state": "ERROR", **base, "error": "version probe timed out"}
    except OSError as exc:
        return {"state": "ERROR", **base, "error": str(exc)}

def discover_tools() -> dict:
    import platform, sys
    return {"platform": platform.platform(), "python": sys.version.split()[0],
            "tools": {spec.key: probe_tool(spec) for spec in TOOL_SPECS}}
