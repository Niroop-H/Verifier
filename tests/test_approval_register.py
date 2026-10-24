import pytest

from mqv_eda.approval_register import create_approval, get_approval, list_approvals


def test_approval_register_persists_decision_and_event_history(tmp_path):
    db = tmp_path / "approvals.sqlite3"
    created = create_approval(
        db, run_id="run-001", report_sha256="a" * 64,
        actor="independent-reviewer", role="release-reviewer",
        decision="APPROVE", rationale="Required checks reviewed",
        run_operator="operator", policy_author="policy-owner",
    )
    assert created["status"] == "APPROVED"
    assert created["events"][-1]["action"] == "DECISION_RECORDED"
    fetched = get_approval(db, created["id"])
    assert fetched["run_id"] == "run-001"
    assert fetched["report_sha256"] == "a" * 64
    assert fetched["status"] == "APPROVED"
    assert list_approvals(db)[0]["id"] == created["id"]


def test_approval_register_blocks_self_approval(tmp_path):
    result = create_approval(
        tmp_path / "approvals.sqlite3", run_id="run-002", report_sha256="b" * 64,
        actor="operator", role="release-reviewer", decision="APPROVE",
        rationale="Trying self approval", run_operator="operator",
    )
    assert result["status"] == "BLOCKED"
    assert any("run operator" in blocker for blocker in result["blockers"])


@pytest.mark.parametrize("digest", ["", "not-a-hash", "a" * 63])
def test_approval_register_rejects_invalid_report_digest(tmp_path, digest):
    with pytest.raises(ValueError, match="64-character hexadecimal"):
        create_approval(
            tmp_path / "approvals.sqlite3", run_id="run", report_sha256=digest,
            actor="reviewer", role="reviewer", decision="APPROVE", rationale="reviewed",
        )
