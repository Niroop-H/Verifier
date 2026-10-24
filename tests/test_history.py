import json
import pytest

from mqv_eda.history import minimize_failure_cover, regression_history


def test_history_preserves_failures_and_input_order(tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    first.write_text(json.dumps({"checks": [{"stage": "lint", "status": "PASS", "duration_seconds": 2}]}))
    second.write_text(json.dumps({"checks": [{"stage": "sim", "status": "FAIL", "duration_seconds": 3}]}))
    result = regression_history([first, second])
    assert result["runs"][0]["report"] == "first.json"
    assert result["latest_run"]["check_counts"]["FAIL"] == 1
    assert result["latest_run"]["duration_seconds"] == 3


def test_failure_cover_selects_small_subset():
    result = minimize_failure_cover([
        {"test_id": "t1", "failure_ids": ["a", "b"]},
        {"test_id": "t2", "failure_ids": ["b"]},
        {"test_id": "t3", "failure_ids": ["c"]},
    ])
    assert result["covered_failure_id_count"] == 3
    assert result["selected_case_count"] == 2
    assert result["uncovered_failure_ids"] == []


def test_failure_cover_rejects_duplicate_ids():
    with pytest.raises(ValueError, match="Duplicate"):
        minimize_failure_cover([
            {"test_id": "t", "failure_ids": ["a"]},
            {"test_id": "t", "failure_ids": ["b"]},
        ])
