from mqv_eda.tool_catalog import list_tool_catalog

def test_core_execution_adapters_are_explicit():
    tools = {row["key"]: row for row in list_tool_catalog()}
    for name in ("iverilog", "vvp", "verilator", "yosys", "sby", "ghdl", "opensta", "klayout"):
        assert tools[name]["state"] == "EXECUTION_ADAPTER"
def test_catalog_only_tools_are_not_overclaimed():
    tools = {row["key"]: row for row in list_tool_catalog()}
    assert tools["Magic"]["state"] == "CATALOG_ONLY"
    assert tools["OpenRCX"]["state"] == "CATALOG_ONLY"
    assert tools["OpenROAD"]["state"] == "CATALOG_ONLY"
def test_all_entries_explain_validation_scope():
    rows = list_tool_catalog()
    assert rows
    assert all(row.get("state") and row.get("ci_test") for row in rows)
