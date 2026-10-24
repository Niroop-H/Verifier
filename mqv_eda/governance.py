"""Evidence identity, fail-closed policy evaluation, and dependency inventory.

Policy outcomes are engineering workflow gates, not chip sign-off or safety certification.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "mqv-aegis-governance/1.0"
PASS_STATES = {"PASS", "PASSED", "SUCCESS"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_revision(root: Path) -> str | None:
    """Read revision from Git when available; never require Git to be installed."""
    env_revision = os.environ.get("GIT_COMMIT") or os.environ.get("GITHUB_SHA")
    if env_revision:
        return env_revision
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=3, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def inventory_inputs(root: Path, *, exclude_dirs: tuple[str, ...] = (
    ".git", ".venv", "venv", "__pycache__", "node_modules", ".pytest_cache",
)) -> dict[str, Any]:
    """Hash a stable workspace inventory and fail on symlinks rather than follow them."""
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError(f"Input root is not a directory: {root}")
    entries: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root)
        if any(part in exclude_dirs for part in relative.parts):
            continue
        if path.is_symlink():
            raise ValueError(f"Symlink input rejected: {relative.as_posix()}")
        if not path.is_file():
            continue
        entries.append({
            "path": relative.as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    canonical = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
    fingerprint = hashlib.sha256(canonical).hexdigest()
    return {
        "schema": SCHEMA,
        "root_label": root.name,
        "file_count": len(entries),
        "total_bytes": sum(item["size_bytes"] for item in entries),
        "files": entries,
        "input_fingerprint_sha256": fingerprint,
        "limitations": [
            "This is a filesystem snapshot, not proof of a clean Git worktree.",
            "Excluded directories are not represented in the fingerprint.",
            "A hash does not prove the design or tool output is correct.",
        ],
    }


def create_run_identity(root: Path, *, configuration: dict[str, Any] | None = None,
                        toolchain: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create an auditable run envelope bound to inputs, config, and declared toolchain."""
    root = Path(root).resolve()
    inventory = inventory_inputs(root)
    config = configuration or {}
    tools = toolchain or {}
    canonical = json.dumps({
        "inputs": inventory["input_fingerprint_sha256"],
        "configuration": config,
        "toolchain": tools,
        "source_revision": _git_revision(root),
    }, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return {
        "schema": SCHEMA,
        "run_id": str(uuid.uuid4()),
        "created_utc": _utc_now(),
        "source_revision": _git_revision(root),
        "input_fingerprint_sha256": inventory["input_fingerprint_sha256"],
        "input_file_count": inventory["file_count"],
        "configuration": config,
        "toolchain": tools,
        "run_fingerprint_sha256": hashlib.sha256(canonical).hexdigest(),
        "inventory": inventory,
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
    }


def evaluate_policy(report: dict[str, Any], policy: dict[str, Any], *,
                    dry_run: bool = False) -> dict[str, Any]:
    """Evaluate required stages conservatively; absent/unknown evidence cannot pass."""
    if not isinstance(report, dict) or not isinstance(report.get("checks"), list):
        raise ValueError("Report must be a JSON object containing a checks array")
    if not isinstance(policy, dict):
        raise ValueError("Policy must be a JSON object")
    policy_id = policy.get("policy_id")
    version = policy.get("version")
    required = policy.get("required_checks")
    if not isinstance(policy_id, str) or not policy_id.strip():
        raise ValueError("Policy requires a non-empty policy_id")
    if not isinstance(version, (str, int)) or str(version).strip() == "":
        raise ValueError("Policy requires a version")
    if not isinstance(required, list) or not required or any(
        not isinstance(stage, str) or not stage.strip() for stage in required
    ):
        raise ValueError("Policy required_checks must be a non-empty list of stage names")

    stage_map: dict[str, list[dict[str, Any]]] = {}
    for check in report["checks"]:
        if isinstance(check, dict) and isinstance(check.get("stage"), str):
            stage_map.setdefault(check["stage"], []).append(check)

    rules: list[dict[str, Any]] = []
    for stage in required:
        found = stage_map.get(stage, [])
        if len(found) == 0:
            rules.append({"stage": stage, "status": "BLOCKED", "reason": "Required evidence is missing"})
            continue
        if len(found) > 1:
            rules.append({"stage": stage, "status": "BLOCKED", "reason": "Duplicate stage records are ambiguous"})
            continue
        status = found[0].get("status")
        if not isinstance(status, str) or status.upper() not in PASS_STATES:
            rules.append({"stage": stage, "status": "BLOCKED", "reason": f"Required check is not a recognized pass (status={status!r})"})
        else:
            rules.append({"stage": stage, "status": "PASS", "reason": "Required check reports PASS"})
    blockers = [rule for rule in rules if rule["status"] != "PASS"]
    advisory = bool(dry_run)
    eligible = not blockers
    return {
        "schema": SCHEMA,
        "policy": {"policy_id": policy_id, "version": str(version)},
        "evaluated_utc": _utc_now(),
        "mode": "DRY_RUN_ADVISORY" if advisory else "ENFORCING",
        "eligible_for_human_review": eligible,
        "decision": "ELIGIBLE_FOR_HUMAN_REVIEW" if eligible else "BLOCKED",
        "rules": rules,
        "blocker_count": len(blockers),
        "required_check_count": len(required),
        "limitations": [
            "Eligibility is not approval, tape-out authorization, or fabrication-readiness certification.",
            "The evaluator trusts the supplied report contents; verify report provenance separately.",
            "Human approval and separation-of-duties workflows must be enforced by an authenticated service.",
        ],
    }


def generate_sbom(*, include_environment: bool = True) -> dict[str, Any]:
    """Generate a CycloneDX-inspired JSON inventory of installed Python distributions.

    License and source metadata are marked UNKNOWN when package metadata does not provide them.
    This is not a complete OS/native EDA-tool SBOM.
    """
    components: list[dict[str, Any]] = []
    if include_environment:
        for dist in sorted(importlib.metadata.distributions(),
                           key=lambda d: (d.metadata.get("Name") or "").lower()):
            name = dist.metadata.get("Name") or "UNKNOWN"
            version = dist.version or "UNKNOWN"
            metadata = dist.metadata
            license_value = metadata.get("License") or "UNKNOWN"
            urls = metadata.get_all("Project-URL") or []
            components.append({
                "type": "library",
                "name": name,
                "version": version,
                "purl": f"pkg:pypi/{name.lower().replace('_', '-') }@{version}",
                "licenses": [{"expression": license_value}] if license_value != "UNKNOWN" else [],
                "license_status": "DECLARED" if license_value != "UNKNOWN" else "UNKNOWN_REQUIRES_REVIEW",
                "source_urls": urls,
            })
    # Report native EDA tool presence separately from CycloneDX components: PATH
    # presence is not proof of a trusted binary, version, license, or usable adapter.
    from .tools import TOOL_SPECS
    native_tools = []
    for spec in TOOL_SPECS:
        resolved = shutil.which(spec.executable)
        native_tools.append({
            "key": spec.key,
            "executable": spec.executable,
            "resolved_path": resolved,
            "state": "PATH_PRESENT" if resolved else "NOT_FOUND",
            "purpose": spec.purpose,
            "tier": spec.tier,
            "integration_level": spec.integration_level,
            "version": None,
            "limitations": ["Presence only; version, binary digest, license, and runtime health are not verified."],
        })
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "timestamp": _utc_now(),
            "tools": [{"name": "MAH Quantum Verify", "version": "development"}],
            "component": {"name": "Execution environment", "version": platform.platform()},
        },
        "components": components,
        "component_count": len(components),
        "native_tool_inventory": native_tools,
        "native_tool_count": len(native_tools),
        "native_tools_found_on_path": sum(item["state"] == "PATH_PRESENT" for item in native_tools),
        "limitations": [
            "Python components cover distributions visible to this interpreter only.",
            "Native tool inventory records PATH presence only; it is not a trusted binary or version attestation.",
            "OS packages, FPGA vendor tools, proprietary EDA installations, and PDK contents may be incomplete.",
            "Missing license metadata is unknown, not permission to redistribute.",
            "Validate the component section against the official CycloneDX schema before claiming schema conformance.",
        ],
    }
