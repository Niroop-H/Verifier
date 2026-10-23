"""Command-line interface for evidence-gated readiness assessment.

Input manifests are caller-supplied evidence inventories and are not trusted or
cryptographically authenticated by this command.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .models import Status
from .readiness import EvidenceRecord, assess_readiness

_ALLOWED_ROOT_KEYS = {"scope", "required_units", "evidence"}
_ALLOWED_EVIDENCE_KEYS = {
    "unit_id", "status", "evidence_uri", "input_digest", "tool_version", "reviewed_by"
}


def _nonempty_string(value: Any, field: str, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string" + (" or null" if optional else "") + ".")
    return value.strip()


def assessment_from_manifest(data: Any) -> dict[str, object]:
    """Validate a JSON manifest and return a fail-closed assessment dictionary."""
    if not isinstance(data, dict):
        raise ValueError("Manifest root must be a JSON object.")
    extra = set(data) - _ALLOWED_ROOT_KEYS
    missing = _ALLOWED_ROOT_KEYS - set(data)
    if extra:
        raise ValueError("Unknown manifest key(s): " + ", ".join(sorted(extra)))
    if missing:
        raise ValueError("Missing manifest key(s): " + ", ".join(sorted(missing)))

    scope = _nonempty_string(data["scope"], "scope")
    required = data["required_units"]
    evidence_data = data["evidence"]
    if not isinstance(required, list) or any(not isinstance(x, str) or not x.strip() for x in required):
        raise ValueError("required_units must be an array of non-empty unit ID strings.")
    if not isinstance(evidence_data, list):
        raise ValueError("evidence must be an array of evidence objects.")

    records: list[EvidenceRecord] = []
    for index, item in enumerate(evidence_data):
        label = f"evidence[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{label} must be a JSON object.")
        unknown = set(item) - _ALLOWED_EVIDENCE_KEYS
        if unknown:
            raise ValueError(f"{label} has unknown key(s): " + ", ".join(sorted(unknown)))
        if "unit_id" not in item or "status" not in item:
            raise ValueError(f"{label} requires unit_id and status.")
        unit_id = _nonempty_string(item["unit_id"], f"{label}.unit_id")
        status_text = _nonempty_string(item["status"], f"{label}.status")
        try:
            status = Status(status_text)
        except ValueError as exc:
            allowed = ", ".join(status.value for status in Status)
            raise ValueError(f"{label}.status must be one of: {allowed}.") from exc
        optional_values = {
            key: _nonempty_string(item.get(key), f"{label}.{key}", optional=True)
            for key in ("evidence_uri", "input_digest", "tool_version", "reviewed_by")
        }
        records.append(EvidenceRecord(unit_id=unit_id, status=status, **optional_values))

    return assess_readiness(
        scope=scope,
        required_units=required,
        evidence=records,
    ).to_dict()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mqv-readiness",
        description="Evaluate a declared verification scope against a supplied evidence manifest.",
    )
    parser.add_argument("manifest", type=Path, help="JSON evidence manifest")
    parser.add_argument("--out", type=Path, help="Write JSON assessment to this path (stdout by default)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
        result = assessment_from_manifest(data)
        rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    readiness = result["readiness"]
    print(f"Readiness assessment: {readiness}", file=sys.stderr)
    return 0 if readiness == "EVIDENCE COMPLETE — SIGN-OFF STILL REQUIRED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
