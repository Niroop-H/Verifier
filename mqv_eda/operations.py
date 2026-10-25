"""Evidence lifecycle, review governance, change impact, and operations helpers.

These local-file primitives do not replace authenticated server-side authorization or OS sandboxing.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "mqv-aegis-operations/1.0"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f".{uuid.uuid4().hex}.tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)


def evidence_scorecard(root: Path, expected_paths: list[str], *,
                       max_age_seconds: int | None = None,
                       now_epoch: float | None = None) -> dict[str, Any]:
    """Explain evidence completeness item by item; never infer correctness from presence."""
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError(f"Evidence root is not a directory: {root}")
    if max_age_seconds is not None and max_age_seconds < 0:
        raise ValueError("max_age_seconds must be non-negative")
    current = time.time() if now_epoch is None else now_epoch
    rows = []
    for item in expected_paths:
        if not isinstance(item, str) or not item or Path(item).is_absolute() or ".." in Path(item).parts:
            raise ValueError(f"Unsafe expected evidence path: {item!r}")
        path = root / item
        if path.is_symlink():
            status, reason = "INVALID", "Symlink evidence is not accepted"
        elif not path.exists():
            status, reason = "MISSING", "Required evidence file does not exist"
        elif not path.is_file():
            status, reason = "INVALID", "Expected evidence path is not a regular file"
        else:
            age = max(0.0, current - path.stat().st_mtime)
            status = "PRESENT"
            reason = "Evidence file exists; content validity is not implied"
            if max_age_seconds is not None and age > max_age_seconds:
                status, reason = "STALE", f"Evidence age {int(age)}s exceeds configured {max_age_seconds}s"
            rows.append({"path": item, "status": status, "reason": reason,
                         "size_bytes": path.stat().st_size, "age_seconds": round(age, 3),
                         "sha256": _hash(path)})
            continue
        rows.append({"path": item, "status": status, "reason": reason})
    present = sum(row["status"] == "PRESENT" for row in rows)
    blockers = [row for row in rows if row["status"] != "PRESENT"]
    return {
        "schema": SCHEMA, "generated_utc": now_utc(), "root_label": root.name,
        "expected_count": len(rows), "present_count": present,
        "completeness_percent": round(100 * present / len(rows), 2) if rows else None,
        "blocker_count": len(blockers), "items": rows,
        "limitations": ["Presence and freshness do not establish evidence correctness or sign-off.",
                        "File modification times may be altered; use signed manifests for stronger provenance."],
    }


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_provenance(root: Path, *, run_identity: dict[str, Any] | None = None,
                     report_path: Path | None = None, bundle_path: Path | None = None) -> dict[str, Any]:
    """Link run identity, report, and bundle by IDs/hashes where available."""
    root = Path(root).resolve()
    def artifact(path):
        if path is None:
            return {"status": "NOT_AVAILABLE"}
        path = Path(path).resolve()
        if not path.is_file():
            return {"status": "MISSING", "path_label": path.name}
        return {"status": "PRESENT", "path_label": path.name, "size_bytes": path.stat().st_size, "sha256": _hash(path)}
    return {
        "schema": SCHEMA, "provenance_id": str(uuid.uuid4()), "created_utc": now_utc(),
        "source_revision": (run_identity or {}).get("source_revision"),
        "run_id": (run_identity or {}).get("run_id"),
        "run_fingerprint_sha256": (run_identity or {}).get("run_fingerprint_sha256"),
        "report": artifact(report_path), "evidence_bundle": artifact(bundle_path),
        "limitations": ["This record links available artifacts but does not sign them.",
                        "A missing source revision is explicitly unknown, not inferred.",
                        "Trust requires independent signature/key verification where required."],
    }


def evaluate_approval(*, policy_decision: dict[str, Any], actor: str, role: str,
                      run_operator: str | None, policy_author: str | None,
                      rationale: str, approved: bool, require_separation: bool = True) -> dict[str, Any]:
    """Create a review decision with optional separation-of-duties enforcement."""
    if not actor.strip() or not role.strip() or not rationale.strip():
        raise ValueError("actor, role, and rationale are required")
    if not isinstance(policy_decision, dict) or policy_decision.get("decision") != "ELIGIBLE_FOR_HUMAN_REVIEW":
        raise ValueError("Approval cannot proceed: policy decision is not eligible for human review")
    if role.lower() not in {"reviewer", "approver", "release_manager"}:
        raise ValueError("Actor role is not authorized to approve")
    conflicts = []
    if require_separation and actor in {run_operator, policy_author}:
        conflicts.append("Approver must differ from run operator and policy author")
    accepted = approved and not conflicts
    return {
        "schema": SCHEMA, "approval_id": str(uuid.uuid4()), "timestamp_utc": now_utc(),
        "actor": actor, "role": role, "approved_requested": bool(approved),
        "approved": accepted, "status": "APPROVED" if accepted else ("REJECTED" if not approved else "BLOCKED"),
        "rationale": rationale, "policy_id": policy_decision.get("policy", {}).get("policy_id"),
        "policy_version": policy_decision.get("policy", {}).get("version"),
        "conflicts": conflicts,
        "limitations": ["This local record is not authenticated identity or durable server-side access control.",
                        "Persist through a protected append-only audit service for operational use."],
    }


def validate_waiver(waiver: dict[str, Any], *, now_epoch: float | None = None,
                    requested_scope: str | None = None) -> dict[str, Any]:
    """Validate waiver fields and expiry; an invalid waiver never clears a policy blocker."""
    required = ("waiver_id", "owner", "reason", "scope", "expires_at_epoch")
    missing = [key for key in required if key not in waiver or waiver[key] in (None, "")]
    issues = [f"Missing required field: {key}" for key in missing]
    expiry = waiver.get("expires_at_epoch")
    try:
        expiry_value = float(expiry)
    except (TypeError, ValueError):
        expiry_value = None
        issues.append("expires_at_epoch must be a Unix timestamp")
    now = time.time() if now_epoch is None else now_epoch
    if expiry_value is not None and expiry_value <= now:
        issues.append("Waiver is expired")
    if requested_scope and waiver.get("scope") != requested_scope:
        issues.append("Waiver scope does not match requested scope")
    return {"schema": SCHEMA, "valid": not issues, "status": "VALID" if not issues else "INVALID",
            "issues": issues, "waiver_id": waiver.get("waiver_id"),
            "limitations": ["Validation does not establish that the waiver owner is authorized.",
                            "A waiver must not override non-waivable safety or legal requirements."]}


def map_change_impact(changed_paths: list[str], rules: dict[str, list[str]]) -> dict[str, Any]:
    """Map changed paths to checks using explicit glob rules; unmapped changes require review."""
    import fnmatch
    mapped: dict[str, set[str]] = {}
    unmapped = []
    for path in changed_paths:
        if not isinstance(path, str) or path.startswith("/") or ".." in Path(path).parts:
            raise ValueError(f"Unsafe changed path: {path!r}")
        matched = False
        for pattern, checks in rules.items():
            if fnmatch.fnmatch(path, pattern):
                matched = True
                for check in checks:
                    mapped.setdefault(check, set()).add(path)
        if not matched:
            unmapped.append(path)
    return {"schema": SCHEMA, "changed_paths": changed_paths,
            "required_checks": [{"check": name, "triggered_by": sorted(paths)} for name, paths in sorted(mapped.items())],
            "unmapped_paths": unmapped,
            "decision": "REVIEW_REQUIRED" if unmapped else "MAPPED",
            "limitations": ["Rules are user-authored heuristics and do not prove all dependencies were captured.",
                            "Unmapped changes must not be treated as safe to skip."]}


def cleanup_workspace(workspace: Path, allowed_root: Path, *, dry_run: bool = True) -> dict[str, Any]:
    """Safely remove one workspace only when it is a strict child of a configured root."""
    root = Path(allowed_root).resolve()
    target_input = Path(workspace)
    if target_input.is_symlink():
        raise ValueError("Workspace root cannot be a symlink")
    target = target_input.resolve()
    if target == root or not target.is_relative_to(root):
        raise ValueError("Workspace must be a strict child of allowed_root")
    if not target.exists():
        return {"schema": SCHEMA, "status": "NOT_FOUND", "path_label": target.name, "dry_run": dry_run}
    if not target.is_dir():
        raise ValueError("Workspace target must be a directory")
    size = sum(p.stat().st_size for p in target.rglob("*") if p.is_file() and not p.is_symlink())
    if any(p.is_symlink() for p in target.rglob("*")):
        raise ValueError("Workspace contains symlinks; refuse cleanup until reviewed")
    if not dry_run:
        shutil.rmtree(target)
    return {"schema": SCHEMA, "status": "WOULD_DELETE" if dry_run else "DELETED",
            "path_label": target.name, "bytes_affected": size, "dry_run": dry_run,
            "limitations": ["Run only in a dedicated worker workspace root with appropriate OS permissions.",
                            "This helper does not provide secure media sanitization or retention legal review."]}


def estimate_resources(*, source_bytes: int, file_count: int, requested_timeout_seconds: int,
                       profile: str = "generic") -> dict[str, Any]:
    """Provide deliberately coarse planning estimates; configured hard limits remain authoritative."""
    if min(source_bytes, file_count, requested_timeout_seconds) < 0:
        raise ValueError("Resource inputs must be non-negative")
    factor = {"generic": 1.0, "simulation": 1.5, "formal": 3.0, "physical": 4.0}.get(profile)
    if factor is None:
        raise ValueError(f"Unknown profile: {profile}")
    # Conservative planning band, not a learned performance model.
    base_memory_mb = 512 + (source_bytes / (1024 * 1024)) * 2 + file_count * 0.05
    estimated_memory_mb = int(base_memory_mb * factor)
    estimated_cpu_cores = min(8, max(1, int(factor + file_count / 5000)))
    return {"schema": SCHEMA, "profile": profile, "estimated_memory_mb": estimated_memory_mb,
            "estimated_cpu_cores": estimated_cpu_cores,
            "suggested_timeout_seconds": int(max(requested_timeout_seconds, 60) * factor),
            "uncertainty": "HIGH", "basis": "Static heuristic; no historical calibration data used.",
            "hard_limits_required": True,
            "limitations": ["Estimate must not be used as a security boundary or guarantee.",
                            "Actual needs depend on design, constraints, tool version, and workload."]}


def record_retention_action(path: Path, *, action: str, reason: str, actor: str,
                            retention_until_utc: str | None = None) -> dict[str, Any]:
    """Create a retention/archival/deletion decision record without silently deleting evidence."""
    if action not in {"retain", "archive", "delete"}:
        raise ValueError("action must be retain, archive, or delete")
    if not reason.strip() or not actor.strip():
        raise ValueError("actor and reason are required")
    path = Path(path)
    return {"schema": SCHEMA, "recorded_utc": now_utc(), "action": action,
            "path_label": path.name, "exists": path.exists(),
            "sha256_before_action": _hash(path) if path.is_file() else None,
            "actor": actor, "reason": reason, "retention_until_utc": retention_until_utc,
            "limitations": ["This records intent only; it does not archive or delete the target.",
                            "Production retention needs authenticated identity, access control, and audit persistence."]}


def apply_retention_action(path: Path, *, action: str, reason: str, actor: str,
                           archive_to: Path | None = None,
                           expected_sha256: str | None = None,
                           dry_run: bool = True) -> dict[str, Any]:
    """Apply a guarded file-level retention action; dry-run is the default.

    Archive copies one regular file to a new, non-existing destination and verifies
    the copied digest before reporting success. Delete requires the caller to supply
    the current SHA-256 as an explicit confirmation token. Directories, symlinks,
    and destination overwrites are rejected.
    """
    if action not in {"retain", "archive", "delete"}:
        raise ValueError("action must be retain, archive, or delete")
    if not isinstance(reason, str) or not reason.strip() or not isinstance(actor, str) or not actor.strip():
        raise ValueError("actor and reason are required")
    source_input = Path(path)
    if source_input.is_symlink():
        raise ValueError("retention target cannot be a symlink")
    source = source_input.resolve(strict=False)
    if not source.exists():
        raise ValueError("retention target does not exist")
    if not source.is_file():
        raise ValueError("retention action supports regular files only")
    before = _hash(source)
    result: dict[str, Any] = {
        "schema": SCHEMA, "action": action, "status": "WOULD_APPLY" if dry_run else "PENDING",
        "source_label": source.name, "sha256_before_action": before,
        "actor": actor.strip(), "reason": reason.strip(), "dry_run": dry_run,
    }
    if action == "retain":
        result["status"] = "RETAINED" if not dry_run else "WOULD_RETAIN"
        return result
    if action == "archive":
        if archive_to is None:
            raise ValueError("archive_to is required for archive action")
        dest_input = Path(archive_to)
        if dest_input.exists() or dest_input.is_symlink():
            raise ValueError("archive destination must not already exist")
        dest_parent = dest_input.parent.resolve(strict=False)
        if not dest_parent.exists() or not dest_parent.is_dir():
            raise ValueError("archive destination parent must already exist")
        dest = dest_parent / dest_input.name
        result["destination_label"] = dest.name
        if dry_run:
            result["status"] = "WOULD_ARCHIVE"
            return result
        shutil.copy2(source, dest)
        copied = _hash(dest)
        if copied != before:
            try:
                dest.unlink()
            finally:
                raise ValueError("archive digest verification failed; copied file removed where possible")
        result.update({"status": "ARCHIVED", "sha256_after_action": copied})
        return result
    if expected_sha256 != before:
        raise ValueError("delete requires --confirm-sha256 matching the current file digest")
    if dry_run:
        result["status"] = "WOULD_DELETE"
        return result
    source.unlink()
    result["status"] = "DELETED"
    return result
