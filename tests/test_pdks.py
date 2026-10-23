from mqv_eda.pdks import PROFILES, inspect_profile, list_profiles

def test_catalog_separates_pdk_from_backend():
    assert PROFILES["sky130"].is_process_pdk
    assert PROFILES["sky130hd"].is_process_pdk
    assert PROFILES["openroad_generic"].is_process_pdk is False

def test_ihp_profile_names_official_drc_and_lvs_requirements(tmp_path):
    result = inspect_profile("ihp_sg13g2", tmp_path)
    assert result["root_found"] is True
    assert result["state"] == "BLOCKED"
    assert any("DRC deck file is missing" in item for item in result["blockers"])
    assert any("LVS script/deck file is missing" in item for item in result["blockers"])
    assert result["signoff_ready"] is False

def test_missing_root_is_blocked_not_ready(tmp_path):
    result = inspect_profile("gf180mcu", tmp_path / "absent")
    assert result["root_found"] is False
    assert result["state"] == "BLOCKED"
    assert result["signoff_ready"] is False

def test_catalog_contains_primary_open_platforms():
    keys = {row["key"] for row in list_profiles()}
    assert {"sky130", "sky130hd", "gf180mcu", "ihp_sg13g2", "asap7", "nangate45", "openroad_generic"} <= keys

def test_unknown_profile_fails_loudly():
    import pytest
    with pytest.raises(ValueError):
        inspect_profile("vendor-x-5nm", ".")

def test_ihp_evidence_claim_is_partial():
    profile = next(row for row in list_profiles() if row["key"] == "ihp_sg13g2")
    assert "partial DRC regression evidence" in profile["evidence"].lower() or "partial" in profile["evidence"].lower()
