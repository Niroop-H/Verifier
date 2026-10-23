from __future__ import annotations
import os
import re
import shutil
import signal
import subprocess
import threading
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Callable
from .models import CheckResult, Status
from .security import sha256_file, safe_extract_zip
from .tools import TOOL_SPECS, probe_tool

EXCLUDED_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "build", "dist", "reports", "artifacts"}
IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*$")

def project_files(root: Path, suffixes: set[str]) -> list[Path]:
    found = []
    root = Path(root)
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in suffixes:
            continue
        if any(part in EXCLUDED_DIRS or part.startswith(".") for part in path.relative_to(root).parts[:-1]):
            continue
        found.append(path.resolve())
    return sorted(found)

def module_names(files: list[Path]) -> list[str]:
    names = []
    pattern = re.compile(r"(?m)^\s*module\s+(?:automatic\s+)?([A-Za-z_$][A-Za-z0-9_$]*)")
    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        names.extend(pattern.findall(text))
    return sorted(set(names))

def looks_like_testbench(path: Path) -> bool:
    name = path.name.lower()
    return name.startswith(("tb_", "testbench_", "test_")) or "_tb." in name or name.endswith("_testbench.v")

def quote_yosys(path: Path) -> str:
    text = str(path.resolve())
    if any(ch in text for ch in ('"', "\n", "\r")):
        raise ValueError("A source path contains characters unsafe for Yosys script syntax.")
    return '"' + text.replace("\\", "\\\\") + '"'

def _hashes(paths: list[Path]) -> dict[str, str]:
    output = {}
    for path in paths:
        try:
            if path.is_file():
                output[str(path.resolve())] = sha256_file(path)
        except OSError:
            continue
    return output

def execute_check(
    stage: str, command: list[str], *, required: bool, inputs: list[Path],
    output_dir: Path, cwd: Path | None = None, timeout: float = 120,
    expected_parser: Callable[[str, int], tuple[Status, str]] | None = None,
) -> CheckResult:
    started = time.monotonic()
    started_utc = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
    exe = command[0] if command else ""
    if not command:
        return CheckResult(stage, Status.ERROR, "Empty command supplied to adapter.", required)
    if not shutil.which(exe):
        return CheckResult(stage, Status.BLOCKED, f"Required executable is unavailable: {exe}", required,
                           command=command, input_hashes=_hashes(inputs), started_utc=started_utc)
    missing = [str(p) for p in inputs if not p.exists() or not p.is_file()]
    if missing:
        return CheckResult(stage, Status.BLOCKED, "Required input file(s) missing: " + ", ".join(missing),
                           required, command=command, input_hashes=_hashes(inputs), started_utc=started_utc)
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / (re.sub(r"[^A-Za-z0-9_.-]+", "_", stage) + ".log")
    version_info = next((probe_tool(s) for s in TOOL_SPECS if s.executable == exe), {})
    version = version_info.get("version")
    proc: subprocess.Popen[bytes] | None = None
    try:
        # Keep subprocess output bounded in memory and on disk. Continue draining
        # after the cap so a noisy tool cannot block forever on a full pipe.
        max_output_bytes = 5 * 1024 * 1024
        captured = bytearray()
        output_truncated = False

        proc = subprocess.Popen(
            command, cwd=str(cwd) if cwd else None,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            env={**os.environ, "LC_ALL": "C", "TZ": "UTC"},
            start_new_session=(os.name == "posix"),
        )

        def drain_output() -> None:
            nonlocal output_truncated
            assert proc is not None and proc.stdout is not None
            while True:
                chunk = proc.stdout.read(65536)
                if not chunk:
                    break
                remaining = max_output_bytes - len(captured)
                if remaining > 0:
                    captured.extend(chunk[:remaining])
                if len(chunk) > remaining:
                    output_truncated = True

        reader = threading.Thread(target=drain_output, name="mqv-output-drain", daemon=True)
        reader.start()
        timed_out = False
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            if os.name == "posix":
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            else:
                proc.kill()
            proc.wait()
        if proc.stdout:
            proc.stdout.close() if os.name != "posix" else None
        reader.join(timeout=5)
        if reader.is_alive():
            # A descendant may have escaped the process group and retained the
            # pipe. Do not block the controller indefinitely on the reader.
            output_truncated = True
        output = captured.decode("utf-8", "replace")
        if output_truncated:
            output += "\\n[OUTPUT TRUNCATED: 5 MiB capture limit]\\n"
        if timed_out:
            output += "\\n[TIMEOUT: process group termination requested]\\n"
        log_path.write_text(output, encoding="utf-8", errors="replace")
        if timed_out:
            return CheckResult(stage, Status.INCONCLUSIVE,
                               f"Command timed out after {timeout}s; process group termination was requested.",
                               required, command=command, tool_version=version, started_utc=started_utc,
                               duration_seconds=round(time.monotonic()-started, 4),
                               exit_code=proc.returncode, input_hashes=_hashes(inputs), log_path=str(log_path),
                               metadata={"output_tail": output[-3000:], "output_truncated": output_truncated})
        if reader.is_alive():
            return CheckResult(stage, Status.INCONCLUSIVE,
                               "Output reader did not terminate; process descendants may still hold output open.",
                               required, command=command, tool_version=version, started_utc=started_utc,
                               duration_seconds=round(time.monotonic()-started, 4),
                               exit_code=proc.returncode, input_hashes=_hashes(inputs), log_path=str(log_path),
                               metadata={"output_tail": output[-3000:], "output_truncated": True})
        if output_truncated and expected_parser:
            return CheckResult(stage, Status.INCONCLUSIVE,
                               "Tool output exceeded the capture limit; verdict parser was not given complete output.",
                               required, command=command, tool_version=version, started_utc=started_utc,
                               duration_seconds=round(time.monotonic()-started, 4),
                               exit_code=proc.returncode, input_hashes=_hashes(inputs), log_path=str(log_path),
                               metadata={"output_tail": output[-3000:], "output_truncated": True})
        if expected_parser:
            status, message = expected_parser(output, proc.returncode)
        elif proc.returncode == 0:
            status, message = Status.PASS, "Command completed successfully."
        else:
            status, message = Status.FAIL, f"Command exited with code {proc.returncode}."
        return CheckResult(stage, status, message, required, command=command, tool_version=version,
                           started_utc=started_utc, duration_seconds=round(time.monotonic()-started, 4),
                           exit_code=proc.returncode, input_hashes=_hashes(inputs), log_path=str(log_path),
                           metadata={"output_tail": output[-3000:], "output_truncated": output_truncated})
    except OSError as exc:
        return CheckResult(stage, Status.ERROR, f"Could not execute tool: {exc}", required,
                           command=command, tool_version=version, started_utc=started_utc,
                           duration_seconds=round(time.monotonic()-started, 4),
                           input_hashes=_hashes(inputs), log_path=str(log_path))

def run_sta(netlist: Path, liberty: Path, sdc: Path, top: str, output_dir: Path,
            timeout: float = 120) -> CheckResult:
    if not IDENTIFIER.fullmatch(top):
        return CheckResult("STATIC_TIMING", Status.BLOCKED, "A valid --top is required for STA.", True)
    output_dir.mkdir(parents=True, exist_ok=True)
    tcl = output_dir / "sta_run.tcl"
    def quote(path: Path) -> str:
        value = str(path.resolve())
        if any(c in value for c in ('{', '}', "\n", "\r")):
            raise ValueError("Unsafe characters in input path for Tcl.")
        return "{" + value + "}"
    try:
        tcl.write_text("\n".join([
            "read_liberty " + quote(liberty),
            "read_verilog " + quote(netlist),
            "link_design " + top,
            "read_sdc " + quote(sdc),
            "check_setup",
            "report_checks -path_delay max -fields {slew cap input net fanout} -digits 4",
            "exit",
        ]) + "\n", encoding="utf-8")
    except (OSError, ValueError) as exc:
        return CheckResult("STATIC_TIMING", Status.ERROR, f"Could not prepare STA run: {exc}", True)
    if any(not p.is_file() for p in (netlist, liberty, sdc)):
        return CheckResult("STATIC_TIMING", Status.BLOCKED, "STA needs netlist, Liberty, and SDC files.", True)
    def parse(output: str, rc: int) -> tuple[Status, str]:
        if rc != 0:
            return Status.FAIL, f"OpenSTA exited with code {rc}."
        if re.search(r"slack\s*\(\s*VIOLATED\s*\)", output, re.I):
            return Status.FAIL, "OpenSTA reported negative timing slack on at least one path."
        if re.search(r"slack\s*\(\s*MET\s*\)", output, re.I):
            return Status.PASS, "OpenSTA reported timing slack MET for reported paths."
        return Status.INCONCLUSIVE, "OpenSTA ran, but no recognized slack verdict was found."
    return execute_check("STATIC_TIMING", ["sta", "-no_splash", "-exit", str(tcl)], required=True,
                         inputs=[netlist, liberty, sdc, tcl], output_dir=output_dir, timeout=timeout,
                         expected_parser=parse)

def _parse_rdb(output: str, rc: int, report_file: Path) -> tuple[Status, str]:
    if rc != 0:
        return Status.FAIL, f"KLayout deck exited with code {rc}."
    if not report_file.is_file():
        return Status.INCONCLUSIVE, "Deck exited successfully but did not produce the agreed report_file."
    try:
        root = ET.parse(report_file).getroot()
        items = root.findall(".//item")
        if items:
            return Status.FAIL, f"KLayout report contains {len(items)} DRC/LVS item(s)."
        if root.tag.lower().endswith("report-database"):
            return Status.PASS, "KLayout report database contains zero items."
        return Status.INCONCLUSIVE, "Report parsed but its root is not a recognized KLayout report database."
    except (ET.ParseError, OSError) as exc:
        return Status.INCONCLUSIVE, f"Could not validate KLayout report database: {exc}"

def run_klayout_deck(stage: str, deck: Path, input_file: Path, output_dir: Path,
                     *, netlist_file: Path | None = None, timeout: float = 600) -> CheckResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_file = (output_dir / (stage.lower() + ".lyrdb")).resolve()
    # Contract: the authorized deck consumes input_file and emits report_file as KLayout RDB.
    command = ["klayout", "-b", "-r", str(deck.resolve()),
               "-rd", f"input_file={input_file.resolve()}",
               "-rd", f"report_file={report_file}"]
    inputs = [deck, input_file]
    if netlist_file is not None:
        command.extend(["-rd", f"netlist_file={netlist_file.resolve()}"])
        inputs.append(netlist_file)
    return execute_check(stage, command, required=True, inputs=inputs, output_dir=output_dir,
                         timeout=timeout,
                         expected_parser=lambda out, rc: _parse_rdb(out, rc, report_file))

def run_project(
    source: Path, output_dir: Path, *, top: str | None = None,
    testbenches: list[Path] | None = None, sim_top: str | None = None,
    netlist: Path | None = None, liberty: Path | None = None, sdc: Path | None = None,
    gds: Path | None = None, drc_deck: Path | None = None,
    lvs_deck: Path | None = None, lvs_netlist: Path | None = None,
    timeout: float = 120,
) -> list[CheckResult]:
    source = Path(source).resolve()
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if source.is_file() and source.suffix.lower() == ".zip":
        project_root = output_dir / "workspace" / "source"
        if project_root.exists():
            shutil.rmtree(project_root)
        safe_extract_zip(source, project_root)
    elif source.is_dir():
        project_root = source
    else:
        raise ValueError("Source must be a project directory or a ZIP archive.")
    results: list[CheckResult] = []
    raw_rtl = project_files(project_root, {".v", ".sv"})
    requested_tb = []
    for value in (testbenches or []):
        p = Path(value)
        requested_tb.append((project_root / p).resolve() if not p.is_absolute() else p.resolve())
    rtl = [p for p in raw_rtl if p not in requested_tb and not looks_like_testbench(p)]
    vhdl = project_files(project_root, {".vhd", ".vhdl"})
    formal_tasks = project_files(project_root, {".sby"})
    if not rtl:
        for stage in ("RTL_LINT", "RTL_COMPILE", "SYNTHESIS"):
            results.append(CheckResult(stage, Status.BLOCKED, "No design Verilog/SystemVerilog source files found.", True))
    else:
        selected_top = top
        if selected_top and not IDENTIFIER.fullmatch(selected_top):
            raise ValueError("Top-level name must be a valid Verilog identifier.")
        if selected_top is None:
            mods = module_names(rtl)
            if len(mods) == 1:
                selected_top = mods[0]
            else:
                message = "Multiple or no modules found; specify --top explicitly."
                for stage in ("RTL_LINT", "RTL_COMPILE", "SYNTHESIS"):
                    results.append(CheckResult(stage, Status.BLOCKED, message, True,
                                               input_hashes=_hashes(rtl)))
        if selected_top is not None:
            results.append(execute_check("RTL_LINT",
                ["verilator", "--lint-only", "-Wno-fatal", "--top-module", selected_top,
                 *map(str, rtl)], required=True, inputs=rtl,
                output_dir=output_dir / "logs", timeout=timeout))
            results.append(execute_check("RTL_COMPILE",
                ["iverilog", "-g2012", "-Wall", "-s", selected_top,
                 "-o", str(output_dir / "rtl_compile.vvp"), *map(str, rtl)],
                required=True, inputs=rtl, output_dir=output_dir / "logs", timeout=timeout))
            ys_script = output_dir / "synthesis.ys"
            try:
                lines = [f"read_verilog -sv {quote_yosys(path)}" for path in rtl]
                lines += [f"hierarchy -check -top {selected_top}", "proc", "opt", "check", "stat",
                          f"write_json {quote_yosys(output_dir / 'synthesis.json')}"]
                ys_script.write_text("\n".join(lines) + "\n", encoding="utf-8")
                results.append(execute_check("SYNTHESIS", ["yosys", "-s", str(ys_script)],
                    required=True, inputs=rtl + [ys_script], output_dir=output_dir / "logs",
                    timeout=timeout))
            except (OSError, ValueError) as exc:
                results.append(CheckResult("SYNTHESIS", Status.ERROR, f"Failed to prepare Yosys script: {exc}", True))
    if requested_tb:
        simtop = sim_top or top
        if not simtop or not IDENTIFIER.fullmatch(simtop):
            results.append(CheckResult("RTL_SIMULATION", Status.BLOCKED,
                "A valid --sim-top is required when testbench files are supplied.", True))
        elif not rtl:
            results.append(CheckResult("RTL_SIMULATION", Status.BLOCKED, "No RTL design files found.", True))
        else:
            all_paths = list(dict.fromkeys(rtl + requested_tb))
            build = output_dir / "simulation.vvp"
            compile_result = execute_check("RTL_SIM_COMPILE",
                ["iverilog", "-g2012", "-s", simtop, "-o", str(build), *map(str, all_paths)],
                required=True, inputs=all_paths, output_dir=output_dir / "logs", timeout=timeout)
            results.append(compile_result)
            if compile_result.status == Status.PASS:
                results.append(execute_check("RTL_SIMULATION", ["vvp", str(build)],
                    required=True, inputs=[build], output_dir=output_dir / "logs", timeout=timeout))
            else:
                results.append(CheckResult("RTL_SIMULATION", compile_result.status,
                    "Simulation was not started because compilation did not pass.", True))
    if vhdl:
        work = output_dir / "ghdl-work"
        work.mkdir(parents=True, exist_ok=True)
        for index, path in enumerate(vhdl):
            results.append(execute_check(f"VHDL_ANALYSIS_{index+1}",
                ["ghdl", "-a", "--std=08", f"--workdir={work}", str(path)],
                required=True, inputs=[path], output_dir=output_dir / "logs", timeout=timeout))
    else:
        results.append(CheckResult("VHDL_ANALYSIS", Status.NOT_RUN, "No VHDL sources were supplied.", False))
    if formal_tasks:
        for index, task in enumerate(formal_tasks):
            results.append(execute_check(f"FORMAL_{index+1}", ["sby", "-f", task.name],
                required=True, inputs=[task], output_dir=output_dir / "logs", cwd=task.parent, timeout=timeout))
    else:
        results.append(CheckResult("FORMAL", Status.NOT_RUN,
            "No .sby task supplied; the platform does not invent formal properties.", False))
    timing_inputs = [netlist, liberty, sdc]
    if any(timing_inputs):
        if not all(timing_inputs):
            results.append(CheckResult("STATIC_TIMING", Status.BLOCKED,
                "Provide all of --netlist, --liberty, and --sdc for timing analysis.", True))
        else:
            results.append(run_sta(Path(netlist), Path(liberty), Path(sdc), top or "", output_dir / "sta",
                                   timeout=timeout))
    else:
        results.append(CheckResult("STATIC_TIMING", Status.NOT_RUN,
            "No gate-level netlist, Liberty library, and SDC constraints supplied.", False))
    if gds or drc_deck:
        if not (gds and drc_deck):
            results.append(CheckResult("PHYSICAL_DRC", Status.BLOCKED,
                "Provide both --gds and --drc-deck; the selected deck must honor input_file/report_file.", True))
        else:
            results.append(run_klayout_deck("PHYSICAL_DRC", Path(drc_deck), Path(gds),
                                            output_dir / "physical", timeout=max(timeout, 600)))
    else:
        results.append(CheckResult("PHYSICAL_DRC", Status.NOT_RUN,
            "No GDSII layout and authorized DRC deck supplied.", False))
    if lvs_deck or lvs_netlist:
        if not (gds and lvs_deck and lvs_netlist):
            results.append(CheckResult("PHYSICAL_LVS", Status.BLOCKED,
                "Provide --gds, --lvs-deck, and --lvs-netlist for LVS.", True))
        else:
            results.append(run_klayout_deck("PHYSICAL_LVS", Path(lvs_deck), Path(gds),
                                            output_dir / "physical", netlist_file=Path(lvs_netlist),
                                            timeout=max(timeout, 600)))
    else:
        results.append(CheckResult("PHYSICAL_LVS", Status.NOT_RUN,
            "No GDSII, source netlist, and authorized LVS deck supplied.", False))
    return results
