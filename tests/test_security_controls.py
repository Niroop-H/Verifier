import json
import os
import pytest
from mqv_eda.security_controls import AccessPolicy, SecurityPolicyError, append_audit_event, redact_secrets, require_access, resolve_under_root, validate_relative_path

@pytest.mark.parametrize("value", ["../secret", "/etc/passwd", "C:\\temp\\x", r"..\\escape", "a/../b", ""])
def test_rejects_unsafe_relative_paths(value):
    with pytest.raises(SecurityPolicyError): validate_relative_path(value)

def test_accepts_nested_relative_path():
    assert validate_relative_path("rtl/top.v") == "rtl/top.v"

def test_resolve_under_root_rejects_symlink_escape(tmp_path):
    root = tmp_path / "workspace"; root.mkdir()
    outside = tmp_path / "outside"; outside.mkdir()
    try: (root / "escape").symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError): pytest.skip("symlinks unavailable")
    with pytest.raises(SecurityPolicyError): resolve_under_root(root, "escape/file.v")

def test_access_policy_denies_unknown_role_and_action():
    policy = AccessPolicy({"reviewer": frozenset({"read_report"})})
    assert policy.permits("reviewer", "read_report")
    assert not policy.permits("reviewer", "run_job")
    with pytest.raises(SecurityPolicyError): require_access(policy, "unknown", "read_report")

def test_redacts_common_secrets():
    redacted = redact_secrets("token=abc123 Bearer eyJhbGciOiJabc password: hunter2")
    assert "abc123" not in redacted and "eyJhbGciOiJabc" not in redacted and "hunter2" not in redacted

def test_audit_event_jsonl_hash_and_redaction(tmp_path):
    log = tmp_path / "audit.jsonl"
    digest = append_audit_event(log, actor="operator", action="export_report", outcome="deny", resource_id="job-42", details={"token": "supersecret", "reason": "policy"})
    record = json.loads(log.read_text().strip())
    assert record["event_sha256"] == digest and record["outcome"] == "deny"
    assert "supersecret" not in log.read_text()
    assert os.stat(log).st_mode & 0o077 == 0
