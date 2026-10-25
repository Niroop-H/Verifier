import json

from mqv_eda.config_validation import validate_project_config


def test_validates_existing_project_inputs(tmp_path):
    (tmp_path / "top.sv").write_text("module top; endmodule")
    result = validate_project_config({"top": "top", "timeout_seconds": 30, "netlist": "top.sv"}, tmp_path)
    assert result["valid"] is True
    assert result["checked_inputs"][0]["path"] == "top.sv"


def test_rejects_path_traversal_and_missing_files(tmp_path):
    result = validate_project_config({"netlist": "../outside.v", "sdc": "missing.sdc"}, tmp_path)
    assert result["valid"] is False
    assert any("safe project-relative" in error for error in result["errors"])
    assert any("does not exist" in error for error in result["errors"])


def test_rejects_invalid_timeout_and_reports_unknown_keys(tmp_path):
    result = validate_project_config({"timeout_seconds": 0, "mystery": True}, tmp_path)
    assert result["valid"] is False
    assert result["warnings"]


def test_rejects_symlink_input(tmp_path):
    target = tmp_path.parent / "target.v"
    target.write_text("module target; endmodule")
    try:
        (tmp_path / "link.v").symlink_to(target)
    except OSError:
        import pytest
        pytest.skip("symlinks unavailable")
    result = validate_project_config({"netlist": "link.v"}, tmp_path)
    assert not result["valid"]
    assert any("symlink" in error.lower() for error in result["errors"])
