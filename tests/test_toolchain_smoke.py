from __future__ import annotations
import os
import shutil
import subprocess
from pathlib import Path
import pytest

from mahqv_eda.engine import (run_ghdl_analysis, run_icarus_simulation,
    run_verilator_lint, run_yosys_synthesis, run_sby, run_sta_script)
from mahqv_eda.models import Status

ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / "examples" / "rtl"
VHDL = ROOT / "examples" / "vhdl"

def require_tool(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    if os.getenv("MQV_REQUIRE_ALL_TOOLS") == "1":
        pytest.fail(f"CI requires '{name}' but it is not installed")
    pytest.skip(f"Optional local dependency not installed: {name}")
    raise AssertionError("unreachable")

def test_icarus_compiles_and_simulates_through_adapter():
    require_tool("iverilog"); require_tool("vvp")
    result = run_icarus_simulation([RTL / "alu.sv", RTL / "tb.sv"], "tb")
    assert result.status == Status.PASS, result.stderr
    assert "MQV_SIM_PASS" in result.stdout

def test_icarus_known_bad_design_is_not_pass(tmp_path):
    require_tool("iverilog")
    bad = tmp_path / "bad.sv"
    bad.write_text("module broken( ; endmodule\n", encoding="utf-8")
    result = run_icarus_simulation([bad], "broken")
    assert result.status == Status.FAIL
    assert "Compilation failed" in result.message

def test_verilator_lints_real_synthesizable_design():
    require_tool("verilator")
    result = run_verilator_lint([RTL / "alu.sv"], "alu")
    assert result.status == Status.PASS, result.stderr

def test_yosys_synthesizes_real_design():
    require_tool("yosys")
    result = run_yosys_synthesis([RTL / "alu.sv"], "alu")
    assert result.status == Status.PASS, result.stderr
    assert "Number of cells" in result.stdout or "Printing statistics" in result.stdout

def test_ghdl_analyzes_and_elaborates_vhdl():
    require_tool("ghdl")
    result = run_ghdl_analysis([ROOT / "examples" / "vhdl" / "logic.vhd"], "logic")
    assert result.status == Status.PASS, result.stderr

def test_z3_executes_smt_query():
    require_tool("z3")
    result = subprocess.run(["z3", "-in"], input="(assert false)\n(check-sat)\n",
        text=True, capture_output=True, check=False, timeout=15)
    assert result.returncode == 0, result.stderr
    assert "unsat" in result.stdout.lower()

def test_sby_proves_tautology(tmp_path):
    require_tool("sby"); require_tool("yosys"); require_tool("z3")
    (tmp_path / "identity.sv").write_text(
        "module top(input [3:0] a); always @* assert(a == a); endmodule\n", encoding="utf-8")
    (tmp_path / "identity.sby").write_text(
        "[options]\nmode prove\ndepth 1\n[engines]\nsmtbmc z3\n"
        "[script]\nread -formal identity.sv\nprep -top top\n[files]\nidentity.sv\n", encoding="utf-8")
    result = run_sby(tmp_path / "identity.sby", timeout=120)
    assert result.status == Status.PASS, result.stdout + result.stderr
    assert (tmp_path / "identity" / "status").is_file()

def test_klayout_creates_a_real_gds_fixture():
    require_tool("klayout")
    script = ROOT / "examples" / "klayout" / "create_layout.rb"
    with __import__("tempfile").TemporaryDirectory(prefix="mqv-klayout-test-") as temp:
        gds = Path(temp) / "sanity.gds"
        proc = subprocess.run(["klayout", "-b", "-r", str(script), "-rd", f"out={gds}"],
            text=True, capture_output=True, timeout=45, check=False)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert gds.is_file() and gds.stat().st_size > 0

def test_opensta_executes_a_real_timing_report():
    require_tool("sta")
    result = run_sta_script(ROOT / "examples" / "sta" / "run.tcl", timeout=45)
    assert result.status == Status.PASS, result.stdout + result.stderr
    assert "Startpoint" in result.stdout
    assert "Endpoint" in result.stdout
