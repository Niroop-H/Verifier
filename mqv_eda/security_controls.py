from __future__ import annotations

"""Fail-closed security primitives for local engineering workflows.

These helpers are not an identity provider, sandbox, or compliance certification.
"""
import hashlib
import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

_SECRET_ASSIGNMENT = re.compile(r"(?i)(token|api[_-]?key|password|passwd|secret|private[_-]?key)(\s*[:=]\s*)([^\s,;]+)")
_BEARER = re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/-]+=*")
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

class SecurityPolicyError(ValueError):
    """Raised when a security policy check cannot safely permit an operation."""

def redact_secrets(text: str) -> str:
    text = _SECRET_ASSIGNMENT.sub(lambda m: f"{m.group(1)}{m.group(2)}[REDACTED]", text)
    return _BEARER.sub(r"\1[REDACTED]", text)

def validate_relative_path(value: str) -> str:
    if not isinstance(value, str) or not value or _CONTROL.search(value):
        raise SecurityPolicyError("Path must be a non-empty string without control characters.")
    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or normalized.startswith("//") or re.match(r"^[A-Za-z]:", normalized):
        raise SecurityPolicyError("Absolute paths are not permitted.")
    if any(part in ("", ".", "..") for part in normalized.split("/")):
        raise SecurityPolicyError("Path traversal or ambiguous path component rejected.")
    return path.as_posix()

def resolve_under_root(root: Path, relative_path: str) -> Path:
    safe = validate_relative_path(relative_path)
    root_resolved = Path(root).resolve()
    target = root_resolved.joinpath(*PurePosixPath(safe).parts)
    resolved = target.resolve()
    if not resolved.is_relative_to(root_resolved):
        raise SecurityPolicyError("Resolved path escapes the permitted workspace.")
    return resolved

@dataclass(frozen=True)
class AccessPolicy:
    """Explicit role/action allow-list; unknown roles/actions deny by default."""
    grants: dict[str, frozenset[str]]
    def permits(self, role: str, action: str) -> bool:
        return bool(role and action and action in self.grants.get(role, frozenset()))

def require_access(policy: AccessPolicy, role: str, action: str) -> None:
    if not policy.permits(role, action):
        raise SecurityPolicyError(f"Access denied for role={role!r}, action={action!r}.")

def append_audit_event(path: Path, *, actor: str, action: str, outcome: str,
                       resource_id: str = "", details: dict[str, object] | None = None) -> str:
    """Append a JSONL event and return its SHA-256; deployment controls remain external."""
    if not actor.strip() or not action.strip() or outcome not in {"allow", "deny", "success", "failure"}:
        raise SecurityPolicyError("Audit actor/action must be set and outcome must be recognized.")
    def sanitize(value):
        if isinstance(value, dict):
            return {str(k): ("[REDACTED]" if re.search(r"(?i)(token|api[_-]?key|password|passwd|secret|private[_-]?key)", str(k)) else sanitize(v))
                    for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [sanitize(item) for item in value]
        if isinstance(value, str):
            return redact_secrets(value)
        return value
    safe_details = sanitize(details or {})
    event = {"timestamp_unix": time.time(), "actor": redact_secrets(actor),
             "action": redact_secrets(action), "outcome": outcome,
             "resource_id": redact_secrets(resource_id), "details": safe_details}
    canonical = json.dumps(event, sort_keys=True, separators=(",", ":"))
    event_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    record = {**event, "event_sha256": event_hash}
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return event_hash
