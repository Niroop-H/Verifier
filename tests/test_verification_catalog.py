from mqv_eda.verification_catalog import (
    catalogue_summary,
    get_verification_unit,
    list_verification_units,
)


def test_catalogue_has_unique_stable_ids_and_required_evidence():
    units = list_verification_units()
    ids = [unit.unit_id for unit in units]
    assert len(units) >= 20
    assert len(ids) == len(set(ids))
    for unit in units:
        assert unit.domain
        assert unit.title
        assert unit.purpose
        assert unit.required_inputs
        assert unit.evidence
        assert unit.integration in {"IMPLEMENTED", "CATALOG_ONLY", "EXTERNAL_EVIDENCE"}


def test_catalogue_includes_full_lifecycle_domains():
    domains = {unit.domain for unit in list_verification_units()}
    assert {
        "front_end", "functional", "formal", "clock_reset", "testability",
        "implementation", "timing", "physical", "signoff", "reliability",
        "assurance", "silicon",
    } <= domains


def test_critical_signoff_units_are_not_mislabelled_as_implemented():
    units = {unit.unit_id: unit for unit in list_verification_units()}
    for unit_id in ("FUNCTIONAL_COVERAGE", "RTL_NETLIST_EQUIV", "CDC", "RDC_RESET",
                    "DFT_SCAN", "POWER_ESTIMATION", "PHYSICAL_LVS", "RELIABILITY_EM",
                    "SILICON_QUAL"):
        assert units[unit_id].integration != "IMPLEMENTED"


def test_lookup_and_summary_are_consistent():
    units = list_verification_units()
    assert get_verification_unit("STA_SETUP_HOLD").title == "Static timing analysis"
    assert get_verification_unit("DOES_NOT_EXIST") is None
    summary = catalogue_summary()
    assert summary["TOTAL"] == len(units)
    assert sum(value for key, value in summary.items() if key != "TOTAL") == len(units)
