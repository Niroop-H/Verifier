import pytest

from mqv_eda.models import Status
from mqv_eda.readiness import EvidenceRecord, Readiness, assess_readiness


def record(unit_id, status=Status.PASS, **kwargs):
    return EvidenceRecord(unit_id=unit_id, status=status, **kwargs)


def test_missing_required_evidence_is_incomplete():
    result = assess_readiness(scope="CPU core RTL", required_units=["RTL_LINT", "FORMAL_PROPERTIES"], evidence=[])
    assert result.readiness == Readiness.INCOMPLETE
    assert set(result.missing) == {"RTL_LINT", "FORMAL_PROPERTIES"}
    assert result.to_dict()["fabrication_ready"] is False


def test_pass_without_artifact_or_input_digest_is_not_accepted():
    result = assess_readiness(scope="CPU core RTL", required_units=["RTL_LINT"], evidence=[record("RTL_LINT")])
    assert result.readiness == Readiness.INCOMPLETE
    assert result.missing == ("RTL_LINT",)


def test_failure_dominates_other_statuses():
    result = assess_readiness(
        scope="CPU core RTL", required_units=["RTL_LINT", "SYNTHESIS"],
        evidence=[record("RTL_LINT", Status.PASS, evidence_uri="artifact://lint", input_digest="sha256:abc", reviewed_by="engineer"),
                  record("SYNTHESIS", Status.FAIL, evidence_uri="artifact://synth", input_digest="sha256:def")],
    )
    assert result.readiness == Readiness.NOT_READY
    assert result.failed == ("SYNTHESIS",)


def test_blocked_tool_or_inconclusive_result_never_passes():
    for state in (Status.BLOCKED, Status.ERROR, Status.INCONCLUSIVE):
        result = assess_readiness(scope="STA review", required_units=["STA_SETUP_HOLD"],
            evidence=[record("STA_SETUP_HOLD", state)])
        assert result.readiness == Readiness.BLOCKED


def test_duplicate_records_are_ambiguous_and_missing():
    evidence = [record("RTL_LINT", evidence_uri="artifact://a", input_digest="sha256:a", reviewed_by="x"),
                record("RTL_LINT", evidence_uri="artifact://b", input_digest="sha256:b", reviewed_by="y")]
    result = assess_readiness(scope="RTL", required_units=["RTL_LINT"], evidence=evidence)
    assert result.readiness == Readiness.INCOMPLETE
    assert result.missing == ("RTL_LINT",)


def test_review_is_required_even_when_all_evidence_passes():
    result = assess_readiness(scope="RTL", required_units=["RTL_LINT"], evidence=[
        record("RTL_LINT", evidence_uri="artifact://lint", input_digest="sha256:abc")])
    assert result.readiness == Readiness.REVIEW_REQUIRED
    assert result.unreviewed == ("RTL_LINT",)


def test_complete_evidence_still_never_claims_fabrication_ready():
    result = assess_readiness(scope="RTL lint gate", required_units=["RTL_LINT"], evidence=[
        record("RTL_LINT", evidence_uri="artifact://lint", input_digest="sha256:abc", reviewed_by="qualified-reviewer")])
    assert result.readiness == Readiness.EVIDENCE_COMPLETE
    assert result.to_dict()["fabrication_ready"] is False
    assert "SIGN-OFF STILL REQUIRED" in result.readiness.value


def test_unknown_unit_and_empty_scope_are_rejected():
    with pytest.raises(ValueError):
        assess_readiness(scope="RTL", required_units=["MADE_UP"], evidence=[])
    with pytest.raises(ValueError):
        assess_readiness(scope="  ", required_units=["RTL_LINT"], evidence=[])
    with pytest.raises(ValueError):
        assess_readiness(scope="RTL", required_units=[], evidence=[])
