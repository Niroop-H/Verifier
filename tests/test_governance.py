import json

import pytest

from mqv_eda.governance import evaluate_baseline_freshness, create_run_identity, evaluate_policy, generate_sbom, inventory_inputs, inventory_license_notices


def test_inventory_fingerprint_changes_when_input_changes(tmp_path):
    source = tmp_path / "project"
    source.mkdir()
    rtl = source / "top.sv"
    rtl.write_text("module top; endmodule\n")
    first = inventory_inputs(source)
    rtl.write_text("module top; wire x; endmodule\n")
    second = inventory_inputs(source)
    assert first["file_count"] == 1
    assert first["input_fingerprint_sha256"] != second["input_fingerprint_sha256"]


def test_inventory_rejects_symlink(tmp_path):
    source = tmp_path / "project"
    source.mkdir()
    target = tmp_path / "outside"
    target.write_text("private")
    link = source / "input.sv"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("symlinks unavailable")
    with pytest.raises(ValueError, match="Symlink"):
        inventory_inputs(source)


def test_run_identity_binds_configuration_and_toolchain(tmp_path):
    (tmp_path / "top.v").write_text("module top; endmodule")
    first = create_run_identity(tmp_path, configuration={"top": "top"}, toolchain={"iverilog": "12"})
    second = create_run_identity(tmp_path, configuration={"top": "other"}, toolchain={"iverilog": "12"})
    assert first["run_id"] != second["run_id"]
    assert first["run_fingerprint_sha256"] != second["run_fingerprint_sha256"]
    assert first["input_fingerprint_sha256"] == second["input_fingerprint_sha256"]


@pytest.mark.parametrize("report", [
    {"checks": []},
    {"checks": [{"stage": "lint", "status": "PASS"}]},
    {"checks": [{"stage": "lint", "status": "PASS"}, {"stage": "lint", "status": "PASS"}]},
    {"checks": [{"stage": "lint", "status": "UNKNOWN"}]},
    {"checks": [{"stage": "lint", "status": "INCONCLUSIVE"}]},
])
def test_policy_fails_closed_for_missing_duplicate_or_unknown_evidence(report):
    result = evaluate_policy(report, {"policy_id": "release", "version": 1, "required_checks": ["lint", "simulation"]})
    assert result["decision"] == "BLOCKED"
    assert result["eligible_for_human_review"] is False
    assert result["blocker_count"] >= 1


def test_policy_pass_only_means_eligible_for_human_review():
    report = {"checks": [{"stage": "lint", "status": "PASS"}, {"stage": "simulation", "status": "PASS"}]}
    result = evaluate_policy(report, {"policy_id": "release", "version": "2", "required_checks": ["lint", "simulation"]})
    assert result["decision"] == "ELIGIBLE_FOR_HUMAN_REVIEW"
    assert "not approval" in " ".join(result["limitations"]).lower()


def test_policy_dry_run_is_explicitly_advisory():
    result = evaluate_policy({"checks": []}, {"policy_id": "release", "version": 1, "required_checks": ["lint"]}, dry_run=True)
    assert result["mode"] == "DRY_RUN_ADVISORY"
    assert result["decision"] == "BLOCKED"


def test_sbom_marks_unknown_license_instead_of_assuming_permission():
    result = generate_sbom()
    assert result["bomFormat"] == "CycloneDX"
    assert result["component_count"] == len(result["components"])
    assert all("license_status" in component for component in result["components"])
    assert "not permission to redistribute" in " ".join(result["limitations"])
    assert result["native_tool_count"] > 0
    assert result["native_tool_count"] == len(result["native_tool_inventory"])
    assert all(item["state"] in {"PATH_PRESENT", "NOT_FOUND"} for item in result["native_tool_inventory"])
    assert all(item["version"] is None for item in result["native_tool_inventory"])
    assert all(item["binary_sha256"] is None or len(item["binary_sha256"]) == 64
               for item in result["native_tool_inventory"])
    assert all(item["binary_digest_state"] in {"HASHED", "NOT_FOUND", "NOT_A_REGULAR_FILE", "HASH_ERROR"}
               for item in result["native_tool_inventory"])
    assert "local executable digest" in " ".join(result["limitations"])


def test_inventory_is_json_serializable(tmp_path):
    (tmp_path / "x.txt").write_text("x")
    json.dumps(inventory_inputs(tmp_path))



def test_baseline_freshness_requires_recent_timestamp_and_matching_revision():
    from datetime import datetime, timezone

    now = datetime(2026, 10, 24, tzinfo=timezone.utc)
    baseline = {"metadata": {"run_identity": {
        "run_id": "baseline-1", "created_utc": "2026-10-23T00:00:00+00:00",
        "source_revision": "abc123",
    }}}
    current = {"metadata": {"run_identity": {"source_revision": "abc123"}}}
    result = evaluate_baseline_freshness(baseline, current, max_age_seconds=3 * 86400, now=now)
    assert result["fresh"] is True
    assert result["source_revision_match"] is True

    stale = evaluate_baseline_freshness(baseline, current, max_age_seconds=3600, now=now)
    assert stale["fresh"] is False
    assert any("stale" in reason.lower() for reason in stale["blockers"])

    changed = {"metadata": {"run_identity": {"source_revision": "def456"}}}
    changed_result = evaluate_baseline_freshness(baseline, changed, now=now)
    assert changed_result["fresh"] is False
    assert any("revision differs" in reason.lower() for reason in changed_result["blockers"])


def test_baseline_freshness_blocks_missing_identity_and_future_timestamps():
    from datetime import datetime, timezone

    now = datetime(2026, 10, 24, tzinfo=timezone.utc)
    missing = evaluate_baseline_freshness({}, {}, now=now)
    assert missing["status"] == "STALE_OR_UNVERIFIABLE"
    future = {"metadata": {"run_identity": {
        "created_utc": "2026-10-25T00:00:00+00:00", "source_revision": "abc"
    }}}
    current = {"metadata": {"run_identity": {"source_revision": "abc"}}}
    result = evaluate_baseline_freshness(future, current, now=now)
    assert not result["fresh"]
    assert any("future" in reason.lower() for reason in result["blockers"])



def test_license_notice_inventory_hashes_files_and_extracts_spdx(tmp_path):
    (tmp_path / "LICENSE").write_text("SPDX-License-Identifier: MIT\n")
    (tmp_path / "vendor").mkdir()
    (tmp_path / "vendor" / "NOTICE.txt").write_text("Third-party attribution required.\n")
    result = inventory_license_notices(tmp_path)
    assert result["notice_file_count"] == 2
    assert result["spdx_declared_count"] == 1
    by_name = {item["path"]: item for item in result["files"]}
    assert by_name["LICENSE"]["spdx_identifiers"] == ["MIT"]
    assert len(by_name["vendor/NOTICE.txt"]["sha256"]) == 64
    assert by_name["vendor/NOTICE.txt"]["license_status"] == "MANUAL_REVIEW_REQUIRED"


def test_license_notice_inventory_rejects_symlinks(tmp_path):
    (tmp_path / "LICENSE").write_text("MIT")
    (tmp_path / "LICENSE-link").symlink_to(tmp_path / "LICENSE")
    with pytest.raises(ValueError, match="Symlink rejected"):
        inventory_license_notices(tmp_path)


def test_inventory_reports_include_dependencies_and_missing_headers(tmp_path):
    (tmp_path / "rtl").mkdir()
    (tmp_path / "rtl" / "include").mkdir()
    (tmp_path / "rtl" / "top.sv").write_text('`include "include/defs.svh"\\nmodule top; endmodule\\n')
    (tmp_path / "rtl" / "include" / "defs.svh").write_text('`define WIDTH 8\\n')
    result = inventory_inputs(tmp_path)
    assert {"source": "rtl/top.sv", "target": "rtl/include/defs.svh"} in result["include_dependencies"]
    assert result["unresolved_includes"] == []
    (tmp_path / "rtl" / "top.sv").write_text('`include "missing.svh"\\nmodule top; endmodule\\n')
    result_missing = inventory_inputs(tmp_path)
    assert result_missing["unresolved_includes"][0]["include"] == "missing.svh"
    assert result_missing["input_fingerprint_sha256"] != result["input_fingerprint_sha256"]


def test_inventory_flags_include_outside_project_root(tmp_path):
    outside = tmp_path.parent / (tmp_path.name + "-outside.svh")
    outside.write_text("`define SECRET 1\\n")
    (tmp_path / "top.sv").write_text(f'`include "{outside.name}"\\n')
    result = inventory_inputs(tmp_path)
    assert result["unresolved_includes"][0]["reason"] == "include resolves outside the project root"
