import json

import pytest

from mqv_eda.governance import create_run_identity, evaluate_policy, generate_sbom, inventory_inputs


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
    assert "PATH presence only" in " ".join(result["limitations"])


def test_inventory_is_json_serializable(tmp_path):
    (tmp_path / "x.txt").write_text("x")
    json.dumps(inventory_inputs(tmp_path))
