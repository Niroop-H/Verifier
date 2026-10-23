from mahqv_eda.pdks import PROFILES, inspect_profile, list_profiles

def test_catalogue_distinguishes_pdk_from_backend():
    assert PROFILES["sky130"].is_pdk
    assert PROFILES["sky130hd"].is_pdk
    assert not PROFILES["openroad_generic"].is_pdk

def test_ihp_profile_requires_real_decks(tmp_path):
    result = inspect_profile("ihp_sg13g2", tmp_path)
    assert result["root_found"] is True
    assert result["profile_ready"] is False
    assert any("DRC deck not found" in item for item in result["blockers"])
    assert any("LVS deck not found" in item for item in result["blockers"])

def test_unknown_pdk_is_rejected():
    import pytest
    with pytest.raises(ValueError):
        inspect_profile("proprietary-node-unknown", ".")

def test_catalogue_has_common_open_processes():
    keys = {p["key"] for p in list_profiles()}
    assert {"sky130", "sky130hd", "gf180mcu", "ihp_sg13g2", "asap7", "openroad_generic"} <= keys
