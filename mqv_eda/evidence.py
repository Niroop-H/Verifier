from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .models import CheckResult, Status, aggregate_status, utc_now
from .security import sha256_file

MANIFEST_SCHEMA_VERSION = "1.0"


def build_evidence_manifest(
    output_dir: Path,
    results: list[CheckResult],
    metadata: dict[str, Any] | None = None,
    *,
    generated_utc: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic-content evidence manifest for one verification run.

    The manifest records hashes for report inputs that still exist and for the
    generated report files. It deliberately does not claim that hashes prove
    design correctness, tool trustworthiness, or a validated execution host.
    """
    root = Path(output_dir).resolve()
    metadata = metadata or {}
    checks: list[dict[str, Any]] = []

    for result in results:
        inputs: list[dict[str, str]] = []
        # CheckResult currently stores input hashes keyed by absolute path.
        for source_path, expected_hash in sorted(result.input_hashes.items()):
            item = {"path": _display_path(source_path, root), "sha256": expected_hash}
            try:
                path = Path(source_path)
                if path.is_file():
                    item["observed_sha256"] = sha256_file(path)
                    item["exists_at_manifest_time"] = "true"
                else:
                    item["exists_at_manifest_time"] = "false"
            except OSError:
                item["exists_at_manifest_time"] = "false"
            inputs.append(item)

        log = None
        if result.log_path:
            log_path = Path(result.log_path)
            if log_path.is_file():
                try:
                    log = {
                        "path": _display_path(str(log_path), root),
                        "sha256": sha256_file(log_path),
                        "size_bytes": log_path.stat().st_size,
                    }
                except OSError:
                    log = None

        checks.append({
            "stage": result.stage,
            "status": result.status.value,
            "required": result.required,
            "message": result.message,
            "exit_code": result.exit_code,
            "tool_version": result.tool_version,
            "duration_seconds": result.duration_seconds,
            "inputs": inputs,
            "log": log,
        })

    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "product": "MAH Quantum Verify",
        "generated_utc": generated_utc or utc_now(),
        "overall_status": aggregate_status(results).value,
        "run_metadata": metadata,
        "checks": checks,
        "evidence_boundary": (
            "Hashes identify recorded bytes; they do not prove correctness, "
            "tool trustworthiness, completeness of verification, foundry sign-off, "
            "or fabrication readiness."
        ),
    }


def _display_path(value: str, root: Path) -> str:
    """Prefer a relative path for artifacts within this run directory."""
    try:
        return Path(value).resolve().relative_to(root).as_posix()
    except (OSError, ValueError):
        # Do not leak absolute host paths for external files into customer reports.
        return Path(value).name


def _write_json(path: Path, document: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def verify_evidence_manifest(path: Path) -> dict[str, Any]:
    """Verify observed hashes embedded in a manifest against current files.

    This verifies a detached evidence bundle only for referenced paths that
    are present relative to the manifest directory. Missing logs are reported
    as missing rather than being interpreted as valid evidence.
    """
    path = Path(path)
    document = json.loads(path.read_text(encoding="utf-8"))
    root = path.parent.resolve()
    problems: list[dict[str, str]] = []
    checked = 0

    for check in document.get("checks", []):
        for item in check.get("inputs", []):
            expected = item.get("observed_sha256")
            rel = item.get("path")
            if not expected or not rel:
                continue
            candidate = (root / rel).resolve()
            if not candidate.is_relative_to(root):
                problems.append({"path": str(rel), "status": "UNSAFE_PATH"})
                continue
            if not candidate.is_file():
                problems.append({"path": str(rel), "status": "MISSING"})
                continue
            checked += 1
            try:
                actual = sha256_file(candidate)
            except OSError:
                problems.append({"path": str(rel), "status": "UNREADABLE"})
                continue
            if actual != expected:
                problems.append({"path": str(rel), "status": "HASH_MISMATCH"})

        log = check.get("log")
        if log:
            rel = log.get("path")
            expected = log.get("sha256")
            if rel and expected:
                candidate = (root / rel).resolve()
                if not candidate.is_relative_to(root):
                    problems.append({"path": str(rel), "status": "UNSAFE_PATH"})
                elif not candidate.is_file():
                    problems.append({"path": str(rel), "status": "MISSING"})
                else:
                    checked += 1
                    try:
                        if sha256_file(candidate) != expected:
                            problems.append({"path": str(rel), "status": "HASH_MISMATCH"})
                    except OSError:
                        problems.append({"path": str(rel), "status": "UNREADABLE"})

    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "manifest": path.name,
        "integrity_status": "PASS" if not problems else "FAIL",
        "items_checked": checked,
        "problems": problems,
        "note": "Integrity verification covers referenced files only; it does not validate design correctness or the trustworthiness of the original run.",
    }
