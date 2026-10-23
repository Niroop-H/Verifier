from mqv_eda.tools import TOOL_SPECS, probe_tool, ToolSpec
from mqv_eda.tool_catalog import list_tool_catalog

def test_tool_specs_have_integration_level():
    assert all(spec.integration_level for spec in TOOL_SPECS)

def test_probe_missing_tool_is_blocked():
    result = probe_tool(ToolSpec("missing", "mqv-executable-definitely-absent-xyz", ("--version",), "test"))
    assert result["state"] == "BLOCKED"
    assert result["integration_level"] == "RUNTIME_DISCOVERY"

def test_catalog_entries_are_marked_honestly():
    catalog = {row["key"]: row for row in list_tool_catalog()}
    assert catalog["iverilog"]["state"] == "EXECUTION_ADAPTER"
    assert catalog["OpenROAD"]["state"] == "CATALOG_ONLY"

