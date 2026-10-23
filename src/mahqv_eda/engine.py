"""Execution adapters that never invoke a shell.

Use only authorized designs and decks. Production services must run this layer
inside isolated, resource-limited workers.
"""
from __future__ import annotations
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Sequence
from .models import EdaResult, Status, utc_now

def run_command(check: str, argv: Sequence[str], *, cwd: Path | None = None,
                timeout: float = 120.0, tool_version: str | None = None) -> EdaResult:
    command = [str(x) for x in argv]
    started_at = utc_now()
    start = time.monotonic()
    executable = shutil.which(command[0]) if command else None
    if not command or not executable:
        return EdaResult(check, Status.BLOCKED,
            f"Required executable not found: {command[0] if command else '(empty command)'}",
            command, started_at=started_at, duration_seconds=time.monotonic()-start,
            tool_version=tool_version)
    command[0] = executable
    try:
        proc = subprocess.run(command, cwd=str(cwd) if cwd else None,
            capture_output=True, text=True, timeout=timeout, check=False)
        elapsed = time.monotonic() - start
        stdout, stderr = (proc.stdout or "")[-20000:], (proc.stderr or "")[-20000:]
        status = Status.PASS if proc.returncode == 0 else Status.FAIL
        return EdaResult(check, status,
            "Command completed successfully" if status == Status.PASS else f"Command exited with code {proc.returncode}",
            command, proc.returncode, started_at, elapsed, stdout, stderr, tool_version)
    except subprocess.TimeoutExpired as exc:
        def text_value(value):
            if isinstance(value, bytes):
                return value.decode(errors="replace")
            return value or ""
        return EdaResult(check, Status.INCONCLUSIVE, f"Timed out after {timeout} seconds",
            command, None, started_at, time.monotonic()-start,
            text_value(exc.stdout)[-20000:], text_value(exc.stderr)[-20000:], tool_version)
    except OSError as exc:
        return EdaResult(check, Status.ERROR, f"Could not execute command: {type(exc).__name__}: {exc}",
            command, None, started_at, time.monotonic()-start, tool_version=tool_version)

def _validated_sources(files: Sequence[str | Path]) -> list[Path]:
    paths = [Path(item).expanduser().resolve() for item in files]
    if not paths:
        raise ValueError("At least one source file is required")
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("Input file(s) not found: " + ", ".join(missing))
    return paths

def _stage_sources(paths: Sequence[Path], directory: Path) -> list[str]:
    staged = []
    for index, path in enumerate(paths):
        suffix = path.suffix.lower()
        safe_suffix = suffix if suffix in {".v", ".sv", ".vh", ".vhd", ".vhdl"} else ".v"
        name = f"source_{index:03d}{safe_suffix}"
        shutil.copyfile(path, directory / name)
        staged.append(name)
    return staged

def run_verilator_lint(files: Sequence[str | Path], top: str, timeout: float = 120.0) -> EdaResult:
    try:
        paths = _validated_sources(files)
    except (ValueError, FileNotFoundError) as exc:
        return EdaResult("rtl_lint", Status.BLOCKED, str(exc), [])
    with tempfile.TemporaryDirectory(prefix="mqv-lint-") as tmp:
        work = Path(tmp)
        staged = _stage_sources(paths, work)
        return run_command("rtl_lint", ["verilator", "--lint-only", "--Wno-fatal",
            "--top-module", top, *staged], cwd=work, timeout=timeout)

def run_icarus_simulation(files: Sequence[str | Path], top: str, timeout: float = 120.0) -> EdaResult:
    try:
        paths = _validated_sources(files)
    except (ValueError, FileNotFoundError) as exc:
        return EdaResult("rtl_simulation", Status.BLOCKED, str(exc), [])
    with tempfile.TemporaryDirectory(prefix="mqv-sim-") as tmp:
        work = Path(tmp)
        staged = _stage_sources(paths, work)
        compile_result = run_command("rtl_compile", ["iverilog", "-g2012", "-s", top,
            "-o", "simulation.vvp", *staged], cwd=work, timeout=timeout)
        if compile_result.status != Status.PASS:
            compile_result.check = "rtl_simulation"
            compile_result.message = "Compilation failed or was blocked; simulation was not run"
            return compile_result
        sim_result = run_command("rtl_simulation", ["vvp", "simulation.vvp"], cwd=work, timeout=timeout)
        sim_result.stdout = compile_result.stdout + sim_result.stdout
        sim_result.stderr = compile_result.stderr + sim_result.stderr
        sim_result.evidence = {"source_files": [p.name for p in paths], "top": top}
        return sim_result

def run_yosys_synthesis(files: Sequence[str | Path], top: str, timeout: float = 180.0) -> EdaResult:
    try:
        paths = _validated_sources(files)
    except (ValueError, FileNotFoundError) as exc:
        return EdaResult("synthesis", Status.BLOCKED, str(exc), [])
    with tempfile.TemporaryDirectory(prefix="mqv-synth-") as tmp:
        work = Path(tmp)
        staged = _stage_sources(paths, work)
        read_cmd = " ".join(f"read_verilog -sv {name};" for name in staged)
        script = f"{read_cmd} hierarchy -check -top {top}; proc; check; synth -top {top}; stat"
        return run_command("synthesis", ["yosys", "-p", script], cwd=work, timeout=timeout)

def run_ghdl_analysis(files: Sequence[str | Path], top: str | None = None, timeout: float = 120.0) -> EdaResult:
    try:
        paths = _validated_sources(files)
    except (ValueError, FileNotFoundError) as exc:
        return EdaResult("vhdl_analysis", Status.BLOCKED, str(exc), [])
    if any(path.suffix.lower() not in {".vhd", ".vhdl"} for path in paths):
        return EdaResult("vhdl_analysis", Status.BLOCKED, "GHDL adapter accepts only .vhd/.vhdl files", [])
    with tempfile.TemporaryDirectory(prefix="mqv-ghdl-") as tmp:
        work = Path(tmp)
        staged = _stage_sources(paths, work)
        result = None
        for name in staged:
            result = run_command("vhdl_analysis", ["ghdl", "-a", "--std=08", name],
                cwd=work, timeout=timeout)
            if result.status != Status.PASS:
                return result
        if top:
            result = run_command("vhdl_elaboration", ["ghdl", "-e", "--std=08", top],
                cwd=work, timeout=timeout)
        assert result is not None
        result.evidence = {"source_count": len(paths), "top": top}
        return result

def run_sby(deck: str | Path, timeout: float = 300.0) -> EdaResult:
    path = Path(deck).expanduser().resolve()
    if not path.is_file() or path.suffix.lower() != ".sby":
        return EdaResult("formal", Status.BLOCKED, "A readable .sby task file is required", [])
    # SBY task files can contain commands. Run only trusted decks in an isolated worker.
    return run_command("formal", ["sby", "-f", path.name], cwd=path.parent, timeout=timeout)

def run_sta_script(script: str | Path, timeout: float = 120.0) -> EdaResult:
    path = Path(script).expanduser().resolve()
    if not path.is_file() or path.suffix.lower() not in {".tcl", ".sta"}:
        return EdaResult("static_timing", Status.BLOCKED, "A readable .tcl/.sta script is required", [])
    # Timing scripts are executable input and must run in isolated workers.
    return run_command("static_timing", ["sta", "-exit", str(path)], timeout=timeout)

def run_klayout_deck(deck: str | Path, layout: str | Path, timeout: float = 300.0) -> EdaResult:
    script = Path(deck).expanduser().resolve()
    gds = Path(layout).expanduser().resolve()
    if not script.is_file():
        return EdaResult("physical_verification", Status.BLOCKED, "Rule deck does not exist", [])
    if not gds.is_file():
        return EdaResult("physical_verification", Status.BLOCKED, "Layout input does not exist", [])
    # KLayout decks are executable code and must run in isolated workers.
    return run_command("physical_verification", ["klayout", "-b", "-r", str(script),
        "-rd", f"input={gds}"], timeout=timeout)
