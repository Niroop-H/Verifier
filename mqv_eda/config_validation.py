"""Preflight validation for declarative project verification configurations."""
from __future__ import annotations
import json
import shutil
from pathlib import Path
from typing import Any

SCHEMA = "mqv-aegis-config/1.0"
PATH_FIELDS = ("testbenches", "netlist", "liberty", "sdc", "gds", "drc_deck", "lvs_deck", "lvs_netlist")


def validate_project_config(config: dict[str, Any], source_root: Path) -> dict[str, Any]:
    """Validate configuration shape and project-local inputs before launching tools."""
    if not isinstance(config, dict):
        raise ValueError("Configuration must be a JSON object")
    root = Path(source_root).resolve()
    if not root.is_dir():
        raise ValueError(f"Source root is not a directory: {root}")
    errors, warnings, checked = [], [], []
    timeout = config.get("timeout_seconds", 120)
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
        errors.append("timeout_seconds must be a positive number")
    top = config.get("top")
    if top is not None and (not isinstance(top, str) or not top.strip()):
        errors.append("top must be a non-empty string when supplied")
    tests = config.get("testbenches", [])
    if not isinstance(tests, list) or any(not isinstance(item, str) or not item for item in tests):
        errors.append("testbenches must be an array of relative path strings")
        tests = []
    values = dict(config)
    for key in PATH_FIELDS:
        if key not in values:
            continue
        raw_values = values[key] if key == "testbenches" else [values[key]]
        if raw_values is None:
            continue
        if not isinstance(raw_values, list):
            raw_values = [raw_values]
        for raw in raw_values:
            if not isinstance(raw, str) or not raw or Path(raw).is_absolute() or ".." in Path(raw.replace("\\", "/")).parts:
                errors.append(f"{key}: expected a safe project-relative path")
                continue
            original = root / raw
            if original.is_symlink():
                errors.append(f"{key}: symlink inputs are not accepted ({raw})")
                continue
            resolved = original.resolve()
            if not resolved.is_relative_to(root):
                errors.append(f"{key}: path escapes source root ({raw})")
                continue
            if not resolved.is_file():
                errors.append(f"{key}: input file does not exist ({raw})")
                continue
            checked.append({"field": key, "path": raw, "size_bytes": resolved.stat().st_size})
    tools = config.get("required_tools", [])
    if not isinstance(tools, list) or any(not isinstance(item, str) or not item for item in tools):
        errors.append("required_tools must be an array of executable names")
        tools = []
    missing_tools = [tool for tool in tools if shutil.which(tool) is None]
    if missing_tools:
        errors.extend([f"Required executable not found on PATH: {tool}" for tool in missing_tools])
    allowed_keys = {"top", "timeout_seconds", *PATH_FIELDS, "required_tools", "sim_top", "policy_id", "policy_version"}
    unknown = sorted(set(config) - allowed_keys)
    if unknown:
        warnings.append("Unknown configuration keys: " + ", ".join(unknown))
    return {
        "schema": SCHEMA, "valid": not errors, "status": "VALID" if not errors else "INVALID",
        "source_label": root.name, "checked_inputs": checked, "errors": errors, "warnings": warnings,
        "limitations": ["Validation is a preflight check; inputs may change before execution.",
                        "It does not validate SDC semantics, Liberty correctness, PDK authorization, or RTL correctness.",
                        "Revalidate and fingerprint inputs at job start to reduce time-of-check/time-of-use risk."],
    }


def load_and_validate_config(config_path: Path, source_root: Path) -> dict[str, Any]:
    try:
        config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read configuration JSON: {exc}") from exc
    return validate_project_config(config, source_root)
