"""Command line interface for the Session 1 EDA engine."""
from __future__ import annotations
import argparse
import json
from typing import Sequence
from .discovery import inspect_all
from .engine import (run_ghdl_analysis, run_icarus_simulation, run_klayout_deck,
    run_sby, run_sta_script, run_verilator_lint, run_yosys_synthesis)
from .models import Status

def _emit(result, as_json: bool) -> int:
    print(json.dumps(result.to_dict(), indent=2) if as_json else
        f"{result.status.value}: {result.check}: {result.message}\n{result.stdout}{result.stderr}")
    return 0 if result.status == Status.PASS else 1

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mqv-eda", description="MAH Quantum Verify Session 1 EDA execution core")
    subs = parser.add_subparsers(dest="operation", required=True)
    doctor = subs.add_parser("doctor", help="discover installed EDA tools")
    doctor.add_argument("--json", action="store_true")
    for command, description in (
        ("lint", "run Verilator lint"), ("simulate", "compile and simulate RTL with Icarus Verilog"),
        ("synth", "synthesize RTL with Yosys"), ("vhdl", "analyze/elaborate VHDL with GHDL")):
        cmd = subs.add_parser(command, help=description)
        if command in {"lint", "simulate", "synth"}:
            cmd.add_argument("--top", required=True)
        else:
            cmd.add_argument("--top")
        cmd.add_argument("files", nargs="+")
    formal = subs.add_parser("formal", help="run an authorized SymbiYosys task")
    formal.add_argument("deck")
    timing = subs.add_parser("timing", help="run an authorized OpenSTA script")
    timing.add_argument("script")
    drc = subs.add_parser("drc", help="run an authorized KLayout rule deck against a layout")
    drc.add_argument("--deck", required=True)
    drc.add_argument("--layout", required=True)
    for command in ("lint", "simulate", "synth", "vhdl", "formal", "timing", "drc"):
        subs.choices[command].add_argument("--json", action="store_true")
    return parser

def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.operation == "doctor":
        tools = inspect_all()
        print(json.dumps(tools, indent=2) if args.json else "\n".join(
            f"{t['name']:<12} {'AVAILABLE' if t['available'] else 'MISSING':<9} {t['version'] or ''}" for t in tools))
        return 0 if any(t["available"] for t in tools) else 1
    if args.operation == "lint":
        result = run_verilator_lint(args.files, args.top)
    elif args.operation == "simulate":
        result = run_icarus_simulation(args.files, args.top)
    elif args.operation == "synth":
        result = run_yosys_synthesis(args.files, args.top)
    elif args.operation == "vhdl":
        result = run_ghdl_analysis(args.files, args.top)
    elif args.operation == "formal":
        result = run_sby(args.deck)
    elif args.operation == "timing":
        result = run_sta_script(args.script)
    elif args.operation == "drc":
        result = run_klayout_deck(args.deck, args.layout)
    else:
        raise AssertionError(args.operation)
    return _emit(result, args.json)

if __name__ == "__main__":
    raise SystemExit(main())
