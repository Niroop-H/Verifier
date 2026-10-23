import json

import pytest

from mqv_eda.readiness_cli import assessment_from_manifest


def manifest(**overrides):
    data = {
        "scope": "RTL lint pilot",
        "required_units": ["RTL_LINT"],
        "evidence": [{
            "unit_id": "RTL_LINT",
            "status": "PASS",
            "evidence_uri": "artifacts/lint.log",
            "input_digest": "sha256:" + "a" * 64,
            "tool_version": "verilator 5.x",
            "reviewed_by": "reviewer@example.test",
        }],
    }
    data.update(overrides)
    return data


def test_complete_manifest_never_claims_fabrication_readiness():
    result = assessment_from_manifest(manifest())
    assert result["readiness"] == "EVIDENCE COMPLETE — SIGN-OFF STILL REQUIRED"
    assert result["fabrication_ready"] is False
    assert result["passed"] == ["RTL_LINT"]


def test_missing_evidence_is_incomplete():
    result = assessment_from_manifest(manifest(evidence=[]))
    assert result["readiness"] == "INCOMPLETE"
    assert result["missing"] == ["RTL_LINT"]
    assert result["fabrication_ready"] is False


def test_pass_without_digest_does_not_pass():
    evidence = manifest()["evidence"]
    evidence[0]["input_digest"] = None
    result = assessment_from_manifest(manifest(evidence=evidence))
    assert result["readiness"] == "INCOMPLETE"
    assert result["missing"] == ["RTL_LINT"]


def test_failed_check_dominates():
    evidence = manifest()["evidence"]
    evidence[0]["status"] = "FAIL"
    result = assessment_from_manifest(manifest(evidence=evidence))
    assert result["readiness"] == "NOT READY"
    assert result["failed"] == ["RTL_LINT"]


def test_unreviewed_evidence_requires_review():
    evidence = manifest()["evidence"]
    evidence[0]["reviewed_by"] = None
    result = assessment_from_manifest(manifest(evidence=evidence))
    assert result["readiness"] == "REVIEW REQUIRED"


@pytest.mark.parametrize("data", [
    [],
    {"scope": "x", "required_units": ["RTL_LINT"], "evidence": [], "fabrication_ready": True},
    {"scope": "x", "required_units": ["RTL_LINT"], "evidence": [{"unit_id": "RTL_LINT", "status": "PASS", "unknown": 1}]},
])
def test_invalid_manifest_shapes_fail_closed(data):
    with pytest.raises(ValueError):
        assessment_from_manifest(data)


def test_unknown_unit_is_rejected():
    with pytest.raises(ValueError, match="Unknown verification unit"):
        assessment_from_manifest(manifest(required_units=["MADE_UP_UNIT"]))


def test_invalid_status_is_rejected():
    evidence = manifest()["evidence"]
    evidence[0]["status"] = "MAYBE"
    with pytest.raises(ValueError, match="status must be one of"):
        assessment_from_manifest(manifest(evidence=evidence))
