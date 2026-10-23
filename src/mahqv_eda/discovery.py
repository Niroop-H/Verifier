"""Runtime discovery; presence does not imply a flow has been validated."""
from __future__ import annotations
import shutil
import subprocess
from dataclasses import dataclass

TOOLS: dict[str, tuple[str, list[str], str]] = {
    "iverilog": ("iverilog", ["-V"], "RTL compilation"),
    "vvp": ("vvp", ["-V"], "RTL simulation runtime"),
    "verilator": ("verilator", ["--version"], "RTL lint and compiled simulation"),
    "yosys": ("yosys", ["-V"], "logic synthesis and structural checks"),
    "ghdl": ("ghdl", ["--version"], "VHDL analysis and simulation"),
    "sby": ("sby", ["--help"], "formal-workflow driver"),
    "z3": ("z3", ["--version"], "SMT solver"),
    "boolector": ("boolector", ["--version"], "SMT solver"),
    "sta": ("sta", ["-version"], "static timing analysis"),
    "klayout": ("klayout", ["-v"], "layout viewing and DRC/LVS deck execution"),
    "openroad": ("openroad", ["-version"], "physical-design flow backend"),
}

@dataclass
class ToolAvailability:
    name: str
    executable: str
    available: bool
    path: str | None
    version: str | None
    purpose: str
    def to_dict(self) -> dict[str, object]:
        return self.__dict__.copy()

def inspect_tool(name: str, timeout: float = 8.0) -> ToolAvailability:
    if name not in TOOLS:
        raise ValueError(f"Unknown tool key: {name}")
    executable, version_args, purpose = TOOLS[name]
    path = shutil.which(executable)
    if path is None:
        return ToolAvailability(name, executable, False, None, None, purpose)
    version = None
    try:
        proc = subprocess.run([path, *version_args], capture_output=True, text=True, timeout=timeout, check=False)
        text = (proc.stdout or "") + "\n" + (proc.stderr or "")
        version = next((line.strip() for line in text.splitlines() if line.strip()), None)
        if proc.returncode != 0 and not version:
            version = f"version probe exited {proc.returncode}"
    except (OSError, subprocess.TimeoutExpired) as exc:
        version = f"probe failed: {type(exc).__name__}"
    return ToolAvailability(name, executable, True, path, version, purpose)

def inspect_all() -> list[dict[str, object]]:
    return [inspect_tool(name).to_dict() for name in TOOLS]
