import json

import pytest

from mqv_eda.regression_intelligence import cluster_failures, detect_flaky_runs, ingest_cobertura_coverage


def test_flaky_detector_reports_variation_without_suppressing_failures(tmp_path):
    first = tmp_path / "one.json"
    second = tmp_path / "two.json"
    first.write_text(json.dumps({"checks": [{"stage": "simulation", "status": "PASS"}]}))
    second.write_text(json.dumps({"checks": [{"stage": "simulation", "status": "FAIL"}]}))
    result = detect_flaky_runs([first, second])
    assert result["variable_stage_count"] == 1
    assert result["stages"][0]["observed_statuses"] == ["FAIL", "PASS"]
    assert "never automatically ignored" in " ".join(result["limitations"])


def test_flaky_detector_requires_multiple_samples(tmp_path):
    one = tmp_path / "one.json"
    one.write_text(json.dumps({"checks": []}))
    with pytest.raises(ValueError, match="At least two"):
        detect_flaky_runs([one])


def test_failure_clustering_normalizes_variable_numbers(tmp_path):
    one, two = tmp_path / "one.log", tmp_path / "two.log"
    one.write_text("ERROR: assertion failed at line 12\n")
    two.write_text("ERROR: assertion failed at line 99\n")
    result = cluster_failures([one, two])
    assert result["cluster_count"] == 1
    assert len(result["clusters"][0]["logs"]) == 2


def test_coverage_import_keeps_missing_metrics_unknown(tmp_path):
    report = tmp_path / "coverage.xml"
    report.write_text('<coverage lines-valid="10" lines-covered="7"/>')
    result = ingest_cobertura_coverage(report)
    assert result["line_coverage"]["ratio"] == 0.7
    assert result["branch_coverage"]["ratio"] is None
    assert result["branch_coverage"]["valid"] is None


def test_coverage_import_rejects_invalid_xml(tmp_path):
    report = tmp_path / "coverage.xml"
    report.write_text("<coverage")
    with pytest.raises(ValueError, match="Cannot parse"):
        ingest_cobertura_coverage(report)
