from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any

from .models import CheckResult, aggregate_status, utc_now
from .security import sha256_file

MANIFEST_SCHEMA_VERSION = "1.0"
DEFAULT_MAX_BUNDLE_BYTES = 100 * 1024 * 1024
MAX_BUNDLE_FILES = 10_000


def build_evidence_manifest(
    output_dir: Path,
    results: list[CheckResult],
    metadata: dict[str, Any] | None = None,
    *,
    generated_utc: str | None = None,
    bundle_inputs: bool = False,
    max_bundle_bytes: int = DEFAULT_MAX_BUNDLE_BYTES,
) -> dict[str, Any]:
    """Build a manifest and optionally copy external inputs into the evidence bundle.

    Bundling is opt-in because RTL, netlists, libraries, PDK collateral and reports
    may be confidential or licence-restricted. The byte limit is preflighted before
    copying. Hashes identify observed bytes; they do not prove design correctness.
    """
    root = Path(output_dir).resolve()
    if max_bundle_bytes < 0:
        raise ValueError("max_bundle_bytes must be zero or greater")

    external_paths: dict[Path, int] = {}
    for result in results:
        for source_path in result.input_hashes:
            source = Path(source_path).resolve()
            if source.is_file() and not _within(source, root):
                external_paths[source] = source.stat().st_size

    if bundle_inputs:
        if len(external_paths) > MAX_BUNDLE_FILES:
            raise ValueError(
                f"Cannot bundle {len(external_paths)} external input files; "
                f"limit is {MAX_BUNDLE_FILES}."
            )
        total_bytes = sum(external_paths.values())
        if total_bytes > max_bundle_bytes:
            raise ValueError(
                f"External inputs total {total_bytes} bytes, exceeding the "
                f"bundle limit of {max_bundle_bytes} bytes. No inputs were copied."
            )
        root.mkdir(parents=True, exist_ok=True)
        for source in sorted(external_paths):
            actual_hash = sha256_file(source)
            safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", source.name).strip("._") or "input"
            destination = root / "evidence-inputs" / f"{actual_hash[:16]}-{safe_name}"
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                if not destination.is_file() or sha256_file(destination) != actual_hash:
                    raise ValueError(f"Evidence bundle destination collision: {destination.name}")
            else:
                shutil.copyfile(source, destination)
                if sha256_file(destination) != actual_hash:
                    destination.unlink(missing_ok=True)
                    raise OSError(f"Copied evidence input failed hash verification: {destination.name}")

    checks: list[dict[str, Any]] = []
    for result in results:
        inputs: list[dict[str, Any]] = []
        for source_path, expected_hash in sorted(result.input_hashes.items()):
            source = Path(source_path).resolve()
            exists = source.is_file()
            observed_hash = sha256_file(source) if exists else None
            changed = observed_hash is not None and observed_hash != expected_hash

            if bundle_inputs and exists and not _within(source, root):
                safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", source.name).strip("._") or "input"
                destination = root / "evidence-inputs" / f"{observed_hash[:16]}-{safe_name}"
                display_path = destination.relative_to(root).as_posix()
                bundled = destination.is_file() and sha256_file(destination) == observed_hash
                if not bundled:
                    display_path = source.name
            else:
                display_path = _display_path(str(source), root)
                bundled = _within(source, root)

            item: dict[str, Any] = {
                "path": display_path,
                "bundled": bundled,
                "sha256_at_check_time": expected_hash,
                "exists_at_manifest_time": exists,
            }
            if observed_hash is not None:
                item["observed_sha256"] = observed_hash
                item["changed_since_check"] = changed
            inputs.append(item)

        log = None
        if result.log_path:
            log_path = Path(result.log_path).resolve()
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
        "bundle": {
            "inputs_bundled": bundle_inputs,
            "max_bundle_bytes": max_bundle_bytes if bundle_inputs else None,
            "external_input_count": len(external_paths),
            "external_input_bytes": sum(external_paths.values()),
        },
        "evidence_boundary": (
            "Hashes identify recorded bytes; they do not prove correctness, "
            "tool trustworthiness, completeness of verification, foundry sign-off, "
            "or fabrication readiness."
        ),
    }


def _within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root)
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
    """Verify bundled inputs/logs; fail for missing, changed or unsafe evidence.

    External source inputs are represented by basename only to avoid leaking
    machine paths. They cannot be re-verified from this bundle, so verification
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
            rel = item.get("path")
            if not rel:
                problems.append({"path": "<missing-path>", "status": "INVALID_MANIFEST_ENTRY"})
                continue
            if item.get("changed_since_check") is True:
                problems.append({"path": str(rel), "status": "INPUT_CHANGED_DURING_RUN"})
            if item.get("exists_at_manifest_time") is False:
                problems.append({"path": str(rel), "status": "MISSING_AT_MANIFEST_TIME"})
                continue
            expected = item.get("observed_sha256")
            if item.get("bundled") is False:
                problems.append({"path": str(rel), "status": "EXTERNAL_UNVERIFIABLE"})
                continue
            if not expected:
                problems.append({"path": str(rel), "status": "HASH_UNAVAILABLE"})
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
            "inputs must be included in the evidence bundle to be independently re-hashed. "
            "This does not validate design correctness or the original execution environment."
        ),
    }
