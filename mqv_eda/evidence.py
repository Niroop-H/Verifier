from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import CheckResult, aggregate_status, utc_now
from .security import sha256_file

MANIFEST_SCHEMA_VERSION = "1.0"


def build_evidence_manifest(
    output_dir: Path,
    results: list[CheckResult],
    metadata: dict[str, Any] | None = None,
    *,
    generated_utc: str | None = None,
) -> dict[str, Any]:
    """Build an evidence manifest with input and log digests for a run.

    Recorded hashes identify observed bytes. They do not prove design correctness,
    tool trustworthiness, or that a verification run was complete.
    """
    root = Path(output_dir).resolve()
    checks: list[dict[str, Any]] = []

    for result in results:
        inputs: list[dict[str, Any]] = []
        for source_path, expected_hash in sorted(result.input_hashes.items()):
            item: dict[str, Any] = {
                "path": _display_path(source_path, root),
                "sha256_at_check_time": expected_hash,
            }
            try:
                source = Path(source_path)
                if source.is_file():
                    item["observed_sha256"] = sha256_file(source)
                    item["exists_at_manifest_time"] = True
                else:
                    item["exists_at_manifest_time"] = False
            except OSError:
                item["exists_at_manifest_time"] = False
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
        "run_metadata": metadata or {},
        "checks": checks,
        "evidence_boundary": (
            "Hashes identify recorded bytes; they do not prove correctness, "
            "tool trustworthiness, completeness of verification, foundry sign-off, "
            "or fabrication readiness."
        ),
    }


def _display_path(value: str, root: Path) -> str:
    """Return relative artifact paths and avoid disclosing host paths for externals."""
    try:
        return Path(value).resolve().relative_to(root).as_posix()
    except (OSError, ValueError):
        return Path(value).name


def _safe_relative(root: Path, value: str) -> Path | None:
    candidate = (root / value).resolve()
    if not candidate.is_relative_to(root):
        return None
    return candidate


def verify_evidence_manifest(path: Path) -> dict[str, Any]:
    """Verify hashes for referenced files present relative to a manifest.

    Only files whose references remain within the manifest directory are opened.
    A recorded file is never considered valid merely because it is missing.
    """
    path = Path(path)
    document = json.loads(path.read_text(encoding="utf-8"))
    root = path.parent.resolve()
    problems: list[dict[str, str]] = []
    checked = 0

    def verify_one(rel: str, expected: str) -> None:
        nonlocal checked
        candidate = _safe_relative(root, rel)
        if candidate is None:
            problems.append({"path": rel, "status": "UNSAFE_PATH"})
            return
        if not candidate.is_file():
            problems.append({"path": rel, "status": "MISSING"})
            return
        try:
            actual = sha256_file(candidate)
        except OSError:
            problems.append({"path": rel, "status": "UNREADABLE"})
            return
        checked += 1
        if actual != expected:
            problems.append({"path": rel, "status": "HASH_MISMATCH"})

    for check in document.get("checks", []):
        for item in check.get("inputs", []):
            expected = item.get("observed_sha256")
            rel = item.get("path")
            if expected and rel:
                verify_one(str(rel), str(expected))
        log = check.get("log")
        if log and log.get("path") and log.get("sha256"):
            verify_one(str(log["path"]), str(log["sha256"]))

    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "manifest": path.name,
        "integrity_status": "PASS" if not problems else "FAIL",
        "items_checked": checked,
        "problems": problems,
        "note": (
            "Integrity verification covers referenced files only; it does not "
            "validate design correctness or the trustworthiness of the original run."
        ),
    }
