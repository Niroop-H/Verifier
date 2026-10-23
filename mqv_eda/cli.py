from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from .engine import run_project
from .models import aggregate_status, Status
from .reporting import write_reports
from .tools import discover_tools

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mqv-eda", description="MAH Quantum Verify local EDA verification runner")
    sub = parser.add_subparsers(dest="command", required=True)
    doctor = sub.add_parser("doctor", help="Discover installed EDA tools and versions")
    doctor.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    verify = sub.add_parser("verify", help="Run applicable EDA checks on a project folder or ZIP")
    verify.add_argument("source", type=Path)
    verify.add_argument("--top", help="Explicit RTL top-level module")
    verify.add_argument("--testbench", type=Path, action="append", default=[], help="Testbench path inside source (repeatable)")
    verify.add_argument("--sim-top", help="Top module for simulation (usually the testbench module)")
    verify.add_argument("--netlist", type=Path, help="Gate-level netlist for STA")
    verify.add_argument("--liberty", type=Path, help="Liberty timing library for STA")
    verify.add_argument("--sdc", type=Path, help="SDC constraints for STA")
    verify.add_argument("--gds", type=Path, help="GDSII layout for physical checks")
    verify.add_argument("--drc-deck", type=Path, help="Authorized KLayout DRC deck using input_file/report_file parameters")
    verify.add_argument("--lvs-deck", type=Path, help="Authorized KLayout LVS deck using input_file/netlist_file/report_file parameters")
    verify.add_argument("--lvs-netlist", type=Path, help="Reference source netlist for LVS")
    verify.add_argument("--out", type=Path, default=Path("mqv-report"))
    verify.add_argument("--timeout", type=float, default=120)
    return parser

def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "doctor":
        info = discover_tools()
        print(json.dumps(info, indent=2))
        return 0 if any(t["state"] == "AVAILABLE" for t in info["tools"].values()) else 2
    try:
        results = run_project(args.source, args.out, top=args.top, testbenches=args.testbench,
                              sim_top=args.sim_top, netlist=args.netlist, liberty=args.liberty,
                              sdc=args.sdc, gds=args.gds, drc_deck=args.drc_deck,
                              lvs_deck=args.lvs_deck, lvs_netlist=args.lvs_netlist, timeout=args.timeout)
        paths = write_reports(args.out, results, {"source": str(args.source.resolve()), "top": args.top})
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    overall = aggregate_status(results)
    print(f"Session 1 overall status: {overall.value}")
    for result in results:
        print(f"{result.status.value:12} {result.stage}: {result.message}")
    print(f"JSON evidence: {paths['json']}")
    print(f"HTML report:   {paths['html']}")
    if overall == Status.PASS:
        return 0
    if overall == Status.FAIL:
        return 1
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
