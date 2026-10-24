from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from .engine import run_project
from .models import aggregate_status, Status
from .reporting import write_reports
from .tools import discover_tools
from .pdks import inspect_profile, list_profiles
from .tool_catalog import list_tool_catalog
from .report_analysis import compare_reports, triage_log, write_json
from .evidence_bundle import create_bundle, verify_bundle
from .evidence_signing import sign_bundle, verify_bundle_signature
from .governance import create_run_identity, evaluate_policy, generate_sbom, inventory_inputs

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mqv-eda", description="MAH Quantum Verify local EDA verification runner")
    sub = parser.add_subparsers(dest="command", required=True)
    doctor = sub.add_parser("doctor", help="Discover installed EDA tools and versions")
    doctor.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    pdks = sub.add_parser("pdks", help="List PDK profiles or inspect a local PDK root")
    pdks.add_argument("--profile", choices=["sky130", "sky130hd", "gf180mcu", "ihp_sg13g2", "asap7", "nangate45", "openroad_generic"])
    pdks.add_argument("--root", type=Path, help="Local PDK/platform root directory")
    pdks.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    catalog = sub.add_parser("tool-catalog", help="List tool integration and validation states")
    catalog.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    bundle = sub.add_parser("bundle", help="Create or verify an integrity-checked evidence ZIP")
    bundle_sub = bundle.add_subparsers(dest="bundle_action", required=True)
    bundle_create = bundle_sub.add_parser("create", help="Create a bundle from an evidence directory")
    bundle_create.add_argument("source", type=Path)
    bundle_create.add_argument("output", type=Path)
    bundle_create.add_argument("--project", help="Optional non-sensitive project label")
    bundle_verify = bundle_sub.add_parser("verify", help="Verify a bundle and its file hashes")
    bundle_verify.add_argument("archive", type=Path)
    sign = sub.add_parser("sign-evidence", help="Create a detached OpenSSL signature for an evidence bundle")
    sign.add_argument("bundle", type=Path)
    sign.add_argument("--private-key", type=Path, required=True)
    sign.add_argument("--signature", type=Path, required=True)
    sigverify = sub.add_parser("verify-evidence-signature", help="Verify a detached evidence signature")
    sigverify.add_argument("bundle", type=Path)
    sigverify.add_argument("--public-key", type=Path, required=True)
    sigverify.add_argument("--signature", type=Path, required=True)
    compare = sub.add_parser("compare", help="Compare two JSON evidence reports and identify regressions")
    compare.add_argument("baseline", type=Path)
    compare.add_argument("candidate", type=Path)
    compare.add_argument("--out", type=Path, default=Path("mqv-compare.json"))
    triage = sub.add_parser("triage", help="Produce evidence-linked deterministic suggestions from a tool log")
    triage.add_argument("log", type=Path)
    triage.add_argument("--out", type=Path, default=Path("mqv-triage.json"))
    inventory = sub.add_parser("inventory", help="Hash project inputs and emit a stable input fingerprint")
    inventory.add_argument("source", type=Path)
    inventory.add_argument("--out", type=Path, default=Path("mqv-input-inventory.json"))
    identity = sub.add_parser("run-identity", help="Create a run ID bound to inputs, config, and declared toolchain")
    identity.add_argument("source", type=Path)
    identity.add_argument("--config", type=Path, help="JSON configuration snapshot")
    identity.add_argument("--toolchain", type=Path, help="JSON toolchain identity snapshot")
    identity.add_argument("--out", type=Path, default=Path("mqv-run-identity.json"))
    policy = sub.add_parser("policy", help="Evaluate a report against a fail-closed JSON policy")
    policy.add_argument("report", type=Path)
    policy.add_argument("policy_file", type=Path)
    policy.add_argument("--dry-run", action="store_true", help="Produce advisory preview; never grants approval")
    policy.add_argument("--out", type=Path, default=Path("mqv-policy-decision.json"))
    sbom = sub.add_parser("sbom", help="Generate a dependency inventory for the active Python environment")
    sbom.add_argument("--out", type=Path, default=Path("mqv-sbom.json"))
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
    if args.command == "sign-evidence":
        try:
            result = sign_bundle(args.bundle, args.private_key, args.signature)
        except (OSError, ValueError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, indent=2))
        return 0
    if args.command == "verify-evidence-signature":
        try:
            result = verify_bundle_signature(args.bundle, args.public_key, args.signature)
        except (OSError, ValueError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, indent=2))
        return 0 if result["valid"] else 2
    if args.command == "bundle":
        try:
            if args.bundle_action == "create":
                result = create_bundle(args.source, args.output, metadata={"project": args.project} if args.project else {})
                print(json.dumps({k: v for k, v in result.items() if k != "manifest"}, indent=2))
                return 0
            result = verify_bundle(args.archive)
        except (OSError, ValueError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, indent=2))
        return 0 if result["status"] == "PASS" else 2
    if args.command == "compare":
        try:
            result = compare_reports(args.baseline, args.candidate)
            write_json(result, args.out)
        except (OSError, ValueError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, indent=2))
        print(f"Comparison evidence: {args.out}")
        return 1 if result["regression_count"] else 0
    if args.command == "triage":
        try:
            result = triage_log(args.log)
            write_json(result, args.out)
        except (OSError, ValueError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, indent=2))
        print(f"Triage evidence: {args.out}")
        return 0
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
