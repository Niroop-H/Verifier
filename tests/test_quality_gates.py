import hashlib
import json

from mqv_eda.quality_gates import evaluate_mutation_results, validate_golden_corpus


def test_mutation_score_and_false_alarm_accounting():
    result = evaluate_mutation_results([
        {"id": "m1", "expected_detection": True, "observed_status": "FAIL"},
        {"id": "m2", "expected_detection": True, "observed_status": "PASS"},
        {"id": "m3", "expected_detection": False, "observed_status": "FAIL"},
        {"id": "m4", "expected_detection": True, "observed_status": "FAIL", "equivalent": True},
    ])
    assert result["mutation_score"] == 0.5
    assert result["killed_count"] == 1
    assert result["survived_count"] == 1
    assert result["false_alarm_count"] == 1


def test_mutation_ids_must_be_unique():
    import pytest
    with pytest.raises(ValueError, match="unique"):
        evaluate_mutation_results([
            {"id": "same", "expected_detection": True, "observed_status": "FAIL"},
            {"id": "same", "expected_detection": True, "observed_status": "PASS"},
        ])


def test_golden_corpus_checks_hash_and_expected_outcome(tmp_path):
    fixture = tmp_path / "good.v"
    fixture.write_text("module good; endmodule\n")
    digest = hashlib.sha256(fixture.read_bytes()).hexdigest()
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"version": "1", "fixtures": [
        {"path": "good.v", "sha256": digest, "expected_outcome": "PASS"}
    ]}))
    result = validate_golden_corpus(tmp_path, manifest)
    assert result["status"] == "PASS"
    assert result["valid_count"] == 1


def test_golden_corpus_fails_on_tampering(tmp_path):
    fixture = tmp_path / "bad.v"
    fixture.write_text("original")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"fixtures": [
        {"path": "bad.v", "sha256": "0" * 64, "expected_outcome": "FAIL"}
    ]}))
    result = validate_golden_corpus(tmp_path, manifest)
    assert result["status"] == "INVALID"
    assert any("mismatched" in issue for issue in result["issues"])
