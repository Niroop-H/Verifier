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
    """Build a manifest for a verification run.

    Both the check-time digest and the generation-time digest are retained when
    an input remains available. This can expose input changes during a run.
    Hashes identify bytes; they do not prove design correctness or tool trust.
    """
    root = Path(output_dir).resolve()
    checks: list[dict[str, Any]] = []

    for result in results:
        inputs: list[dict[str, Any]] = []
        for source_path, expected_hash in sorted(result.input_hashes.items()):
            source = Path(source_path)
            inside_bundle = _within(source, root)
            item: dict[str, Any] = {
                "path": _display_path(source_path, root),
                "bundled": inside_bundle,
                "sha256_at_check_time": expected_hash,
            }
            try:
                if source.is_file():
                    observed = sha256_file(source)
                    item["observed_sha256"] = observed
                    item["exists_at_manifest_time"] = True
                    item["changed_since_check"] = observed != expected_hash
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
                        "bundled": _within(log_path, root),
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


def _within(path: Path, root: Path) -> bool:
    try:
        Path(path).resolve().relative_to(root)
        return True
    except (OSError, ValueError):
        return False


def _display_path(value: str, root: Path) -> str:
    """Return a relative path for bundled files and basename for external files."""
    path = Path(value)
    try:
        return path.resolve().relative_to(root).as_posix()
    except (OSError, ValueError):
        return path.name


def _safe_relative(root: Path, value: str) -> Path | None:
    try:
        candidate = (root / value).resolve()
        candidate.relative_to(root)
        return candidate
    except (OSError, ValueError):
        return None


def verify_evidence_manifest(path: Path) -> dict[str, Any]:
    """Verify bundled inputs/logs; fail for missing bundled evidence.

    External source inputs are represented by basename only to avoid leaking
    machine paths. They cannot be re-verified from this bundle, so this function
    reports them as EXTERNAL_UNVERIFIABLE rather than claiming integrity.
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
            if not expected or not rel:
                continue
            if item.get("bundled") is False:
                problems.append({"path": str(rel), "status": "EXTERNAL_UNVERIFIABLE"})
                continue
            verify_one(str(rel), str(expected))
        log = check.get("log")
        if log and log.get("path") and log.get("sha256"):
            if log.get("bundled") is False:
                problems.append({"path": str(log["path"]), "status": "EXTERNAL_UNVERIFIABLE"})
            else:
                verify_one(str(log["path"]), str(log["sha256"]))

    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "manifest": path.name,
        "integrity_status": "PASS" if not problems else "FAIL",
        "items_checked": checked,
        "problems": problems,
        "note": (
            "Integrity verification covers bundled referenced files only. External "
            "inputs must be supplied in the evidence bundle to be independently re-hashed. "
            "This does not validate design correctness or the original execution environment."
        ),
    }
