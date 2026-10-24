import time

import pytest

from mqv_eda.operations import (
    build_provenance, cleanup_workspace, estimate_resources, evaluate_approval,
    evidence_scorecard, map_change_impact, record_retention_action, validate_waiver,
)


def test_scorecard_explains_missing_and_present(tmp_path):
    (tmp_path / "report.json").write_text("{}")
    result = evidence_scorecard(tmp_path, ["report.json", "missing.json"])
    assert result["present_count"] == 1
    assert result["items"][1]["status"] == "MISSING"
    assert result["completeness_percent"] == 50.0


def test_scorecard_flags_stale_evidence(tmp_path):
    f = tmp_path / "old.json"
    f.write_text("{}")
    result = evidence_scorecard(tmp_path, ["old.json"], max_age_seconds=10, now_epoch=time.time() + 100)
    assert result["items"][0]["status"] == "STALE"


def test_provenance_explicitly_marks_missing_artifact(tmp_path):
    result = build_provenance(tmp_path, report_path=tmp_path / "missing.json")
    assert result["report"]["status"] == "MISSING"
    assert result["evidence_bundle"]["status"] == "NOT_AVAILABLE"


def test_approval_rejects_operator_self_approval():
    decision = {"decision": "ELIGIBLE_FOR_HUMAN_REVIEW", "policy": {"policy_id": "p", "version": "1"}}
    result = evaluate_approval(policy_decision=decision, actor="alice", role="reviewer",
                               run_operator="alice", policy_author="bob", rationale="reviewed", approved=True)
    assert result["status"] == "BLOCKED"
    assert result["approved"] is False


def test_approval_requires_policy_eligibility():
    with pytest.raises(ValueError, match="not eligible"):
        evaluate_approval(policy_decision={"decision": "BLOCKED"}, actor="alice", role="reviewer",
                          run_operator=None, policy_author=None, rationale="review", approved=True)


def test_waiver_expiry_and_scope_are_enforced():
    waiver = {"waiver_id": "W-1", "owner": "lead", "reason": "temporary", "scope": "lint",
              "expires_at_epoch": 100}
    assert not validate_waiver(waiver, now_epoch=101)["valid"]
    assert not validate_waiver({**waiver, "expires_at_epoch": 200}, now_epoch=101, requested_scope="simulation")["valid"]


def test_change_impact_requires_review_for_unmapped_paths():
    result = map_change_impact(["rtl/top.sv", "notes/readme.md"], {"rtl/*.sv": ["lint", "simulation"]})
    assert [x["check"] for x in result["required_checks"]] == ["lint", "simulation"]
    assert result["unmapped_paths"] == ["notes/readme.md"]
    assert result["decision"] == "REVIEW_REQUIRED"


def test_cleanup_refuses_root_or_outside_paths(tmp_path):
    root = tmp_path / "workers"
    root.mkdir()
    with pytest.raises(ValueError, match="strict child"):
        cleanup_workspace(root, root)
    outside = tmp_path / "outside"
    outside.mkdir()
    with pytest.raises(ValueError, match="strict child"):
        cleanup_workspace(outside, root)


def test_cleanup_dry_run_then_delete(tmp_path):
    root = tmp_path / "workers"
    target = root / "job-1"
    target.mkdir(parents=True)
    (target / "output.log").write_text("x")
    dry = cleanup_workspace(target, root)
    assert dry["status"] == "WOULD_DELETE" and target.exists()
    done = cleanup_workspace(target, root, dry_run=False)
    assert done["status"] == "DELETED" and not target.exists()


def test_resource_estimate_is_explicitly_heuristic():
    result = estimate_resources(source_bytes=1_000_000, file_count=100, requested_timeout_seconds=30, profile="formal")
    assert result["hard_limits_required"] is True
    assert result["uncertainty"] == "HIGH"


def test_retention_records_intent_not_deletion(tmp_path):
    target = tmp_path / "report.json"
    target.write_text("data")
    record = record_retention_action(target, action="delete", reason="expired", actor="operator")
    assert record["sha256_before_action"]
    assert target.exists()
