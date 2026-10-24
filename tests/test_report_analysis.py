from __future__ import annotations
import json
from pathlib import Path
import pytest
from mqv_eda.report_analysis import compare_reports, triage_log, write_json

def report(checks, status="PASS"):
    return {"schema_version":"1.0","overall_status":status,"checks":checks}

def check(stage, status, hashes=None, duration=1.0, version="1.0"):
    return {"stage":stage,"status":status,"input_hashes":hashes or {"rtl":"abc"},
            "duration_seconds":duration,"tool_version":version,"message":status}

def test_compare_detects_pass_to_fail_regression(tmp_path):
    old, new = tmp_path/"old.json", tmp_path/"new.json"
    old.write_text(json.dumps(report([check("SIM","PASS")])))
    new.write_text(json.dumps(report([check("SIM","FAIL")], "FAIL")))
    result = compare_reports(old,new)
    assert result["regression_count"] == 1
    assert result["regressions"][0]["candidate_status"] == "FAIL"

def test_compare_marks_removed_check_as_regression(tmp_path):
    old, new = tmp_path/"old.json", tmp_path/"new.json"
    old.write_text(json.dumps(report([check("FORMAL","PASS")])))
    new.write_text(json.dumps(report([])))
    result = compare_reports(old,new)
    assert result["regression_count"] == 1
    assert result["regressions"][0]["change"] == "REMOVED"

def test_compare_detects_input_and_tool_changes(tmp_path):
    old, new = tmp_path/"old.json", tmp_path/"new.json"
    old.write_text(json.dumps(report([check("SIM","PASS", {"rtl":"a"}, 1, "1")])))
    new.write_text(json.dumps(report([check("SIM","PASS", {"rtl":"b"}, 2, "2")])))
    row = compare_reports(old,new)["changes"][0]
    assert row["change"] == "INPUTS_CHANGED"
    assert row["baseline_input_hashes"] != row["candidate_input_hashes"]

def test_compare_rejects_invalid_report(tmp_path):
    bad = tmp_path/"bad.json"
    bad.write_text('{"no_checks": []}')
    with pytest.raises(ValueError):
        compare_reports(bad,bad)

def test_triage_extracts_syntax_error_location(tmp_path):
    log = tmp_path/"sim.log"
    log.write_text("parse error at rtl/core.sv:42:7 unexpected token\n")
    result = triage_log(log)
    assert result["findings"][0]["category"] == "syntax"
    assert result["findings"][0]["source_location"]["line"] == 42
    assert result["log_sha256"]

def test_triage_returns_safe_fallback_for_unknown_log(tmp_path):
    log = tmp_path/"tool.log"
    log.write_text("tool completed with a cryptic message\n")
    result = triage_log(log)
    assert result["findings"][0]["category"] == "no-recognized-pattern"
    assert "manually" in result["findings"][0]["suggestion"]

def test_write_json_creates_parent(tmp_path):
    output = write_json({"ok": True}, tmp_path/"nested"/"result.json")
    assert json.loads(output.read_text()) == {"ok": True}
