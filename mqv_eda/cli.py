from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .engine import run_project
from .models import Status, aggregate_status
from .reporting import write_reports
from .evidence import build_evidence_manifest, verify_evidence_manifest
from .tools import discover_tools
from .pdks import inspect_profile, list_profiles
from .tool_catalog import list_tool_catalog


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mqv-eda",
        description="MAH Quantum Verify local EDA verification runner",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="Discover installed EDA tools and versions")
    doctor.add_argument("--json", action="store_true", help="Emit machine-readable JSON")

    pdks = sub.add_parser("pdks", help="List PDK profiles or inspect a local PDK root")
    pdks.add_argument(
        "--profile",
        choices=["sky130", "sky130hd", "gf180mcu", "ihp_sg13g2", "asap7", "nangate45", "openroad_generic"],
    )
    pdks.add_argument("--root", type=Path, help="Local PDK/platform root directory")
    pdks.add_argument("--json", action="store_true", help="Emit machine-readable JSON")

    catalog = sub.add_parser("tool-catalog", help="List tool integration and validation states")
    catalog.add_argument("--json", action="store_true", help="Emit machine-readable JSON")

    verify = sub.add_parser("verify", help="Run applicable EDA checks on a project folder or ZIP")
    verify.add_argument("source", type=Path)
    verify.add_argument("--top", help="Explicit RTL top-level module")
    verify.add_argument(
        "--testbench", type=Path, action="append", default=[],
        help="Testbench path inside source (repeatable)",
    )
    verify.add_argument("--sim-top", help="Top module for simulation (usually the testbench module)")
    verify.add_argument("--netlist", type=Path, help="Gate-level netlist for STA")
    verify.add_argument("--liberty", type=Path, help="Liberty timing library for STA")
    verify.add_argument("--sdc", type=Path, help="SDC constraints for STA")
    verify.add_argument("--gds", type=Path, help="GDSII layout for physical checks")
    verify.add_argument(
        "--drc-deck", type=Path,
        help="Authorized KLayout DRC deck using input_file/report_file parameters",
    )
    verify.add_argument(
        "--lvs-deck", type=Path,
        help="Authorized KLayout LVS deck using input_file/netlist_file/report_file parameters",
    )
    verify.add_argument("--lvs-netlist", type=Path, help="Reference source netlist for LVS")
    verify.add_argument("--out", type=Path, default=Path("mqv-report"))
    verify.add_argument("--timeout", type=float, default=120)
    verify.add_argument(
        "--bundle-inputs",
        action="store_true",
        help="Copy known external input files into the evidence bundle; use only when you are authorized to duplicate this design collateral",
    )
    verify.add_argument(
        "--max-bundle-mb",
        type=int,
        default=100,
        help="Maximum total bytes of copied external inputs in MiB when --bundle-inputs is enabled (default: 100)",
    )

    integrity = sub.add_parser(
        "verify-evidence", help="Verify hashes in a previously generated evidence manifest",
    )
    integrity.add_argument("manifest", type=Path, help="Path to evidence-manifest.json")
    integrity.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "doctor":
        info = discover_tools()
        print(json.dumps(info, indent=2))
        return 0 if any(t["state"] == "AVAILABLE" for t in info["tools"].values()) else 2

    if args.command == "pdks":
        if args.profile and not args.root:
            print("ERROR: --profile requires --root for local inspection.", file=sys.stderr)
            return 2
        if args.profile:
            result = inspect_profile(args.profile, args.root)
            print(json.dumps(result, indent=2))
            return 0 if result["state"] == "COLLATERAL_PRESENT_NOT_VALIDATED" else 2
        print(json.dumps(list_profiles(), indent=2))
        return 0

    if args.command == "tool-catalog":
        print(json.dumps(list_tool_catalog(), indent=2))
        return 0

    if args.command == "verify-evidence":
        try:
            report = verify_evidence_manifest(args.manifest)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"ERROR: Could not verify evidence manifest: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(report, indent=2))
        return 0 if report["integrity_status"] == "PASS" else 1

    if args.max_bundle_mb < 0:
        print("ERROR: --max-bundle-mb must be zero or greater.", file=sys.stderr)
        return 2

    try:
        results = run_project(
            args.source,
            args.out,
            top=args.top,
            testbenches=args.testbench,
            sim_top=args.sim_top,
            netlist=args.netlist,
            liberty=args.liberty,
            sdc=args.sdc,
            gds=args.gds,
            drc_deck=args.drc_deck,
            lvs_deck=args.lvs_deck,
            lvs_netlist=args.lvs_netlist,
            timeout=args.timeout,
        )
        # Keep host-specific absolute paths out of customer-facing reports.
        metadata = {"source": args.source.name, "top": args.top}
        paths = write_reports(args.out, results, metadata)
        manifest = build_evidence_manifest(
            args.out,
            results,
            metadata,
            bundle_inputs=args.bundle_inputs,
            max_bundle_bytes=args.max_bundle_mb * 1024 * 1024,
        )
        manifest_path = args.out / "evidence-manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    overall = aggregate_status(results)
    print(f"Session 1 overall status: {overall.value}")
    for result in results:
        print(f"{result.status.value:12} {result.stage}: {result.message}")
    print(f"JSON evidence: {paths['json']}")
    print(f"HTML report:   {paths['html']}")
    print(f"Evidence manifest: {manifest_path}")

    if overall == Status.PASS:
        return 0
    if overall == Status.FAIL:
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
