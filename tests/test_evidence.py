from pathlib import Path

from mqv_eda.evidence import build_evidence_manifest, verify_evidence_manifest
from mqv_eda.models import CheckResult, Status


def test_manifest_records_status_and_hashes(tmp_path):
    source = tmp_path / "design.v"
    source.write_text("module top; endmodule\n", encoding="utf-8")
    log = tmp_path / "check.log"
    log.write_text("lint succeeded\n", encoding="utf-8")
    import hashlib
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    result = CheckResult(
        stage="RTL_LINT",
        status=Status.PASS,
        message="Lint completed",
        input_hashes={str(source): source_hash},
        log_path=str(log),
        tool_version="test-tool 1.0",
        exit_code=0,
        duration_seconds=0.25,
    )

    manifest = build_evidence_manifest(
        tmp_path, [result], {"source_revision": "abc123"}, generated_utc="2026-01-01T00:00:00+00:00"
    )

    assert manifest["overall_status"] == "PASS"
    assert manifest["checks"][0]["inputs"][0]["observed_sha256"] == source_hash
    assert manifest["checks"][0]["log"]["sha256"] == hashlib.sha256(log.read_bytes()).hexdigest()
    assert manifest["run_metadata"]["source_revision"] == "abc123"


def test_manifest_preserves_blocked_state(tmp_path):
    result = CheckResult("STATIC_TIMING", Status.BLOCKED, "No liberty file", required=True)
    manifest = build_evidence_manifest(tmp_path, [result])
    assert manifest["overall_status"] == "BLOCKED"


def test_verify_manifest_detects_changed_log_and_input(tmp_path):
    import hashlib
    source = tmp_path / "design.v"
    source.write_text("module top; endmodule\n", encoding="utf-8")
    log = tmp_path / "check.log"
    log.write_text("first result\n", encoding="utf-8")
    result = CheckResult(
        "RTL_LINT", Status.PASS, "done",
        input_hashes={str(source): hashlib.sha256(source.read_bytes()).hexdigest()},
        log_path=str(log),
    )
    document = build_evidence_manifest(tmp_path, [result], generated_utc="2026-01-01T00:00:00+00:00")
    # A portable bundle uses relative paths and observed hashes.
    document["checks"][0]["inputs"][0]["path"] = "design.v"
    document["checks"][0]["inputs"][0]["bundled"] = True
    document["checks"][0]["log"]["path"] = "check.log"
    document["checks"][0]["log"]["bundled"] = True
    manifest_path = tmp_path / "evidence-manifest.json"
    import json
    manifest_path.write_text(json.dumps(document), encoding="utf-8")

    assert verify_evidence_manifest(manifest_path)["integrity_status"] == "PASS"
    source.write_text("module top; assign x = 1; endmodule\n", encoding="utf-8")
    log.write_text("altered result\n", encoding="utf-8")
    report = verify_evidence_manifest(manifest_path)
    assert report["integrity_status"] == "FAIL"
    assert {item["status"] for item in report["problems"]} == {"HASH_MISMATCH"}



def test_verify_manifest_fails_when_input_changed_after_check(tmp_path):
    import hashlib
    source = tmp_path / "design.v"
    source.write_text("module top; endmodule\\n", encoding="utf-8")
    checked_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    # Simulate a design file being modified after the check captured its digest.
    source.write_text("module top; assign x = 1; endmodule\\n", encoding="utf-8")
    result = CheckResult(
        "RTL_LINT",
        Status.PASS,
        "lint completed",
        input_hashes={str(source): checked_hash},
    )
    document = build_evidence_manifest(tmp_path, [result])
    assert document["checks"][0]["inputs"][0]["changed_since_check"] is True
    document["checks"][0]["inputs"][0]["path"] = "design.v"
    document["checks"][0]["inputs"][0]["bundled"] = True
    manifest_path = tmp_path / "evidence-manifest.json"
    manifest_path.write_text(json.dumps(document), encoding="utf-8")

    report = verify_evidence_manifest(manifest_path)
    assert report["integrity_status"] == "FAIL"
    assert any(problem["status"] == "INPUT_CHANGED_DURING_RUN" for problem in report["problems"])


def test_verify_manifest_rejects_path_escape(tmp_path):
    import json
    manifest_path = tmp_path / "evidence-manifest.json"
    manifest_path.write_text(json.dumps({
        "checks": [{"inputs": [{"path": "../outside.txt", "observed_sha256": "0" * 64, "bundled": True}], "log": None}]
    }), encoding="utf-8")
    report = verify_evidence_manifest(manifest_path)
    assert report["integrity_status"] == "FAIL"
    assert report["problems"][0]["status"] == "UNSAFE_PATH"
