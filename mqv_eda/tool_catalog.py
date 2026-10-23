"""Open-source EDA integration catalogue.

Catalogue presence is not a claim of executable integration. Only entries
marked EXECUTION_ADAPTER or SOLVER_ADAPTER have code paths in this release.
"""
TOOL_CATALOG = [
    {"key":"iverilog","category":"RTL compile/simulation","state":"EXECUTION_ADAPTER","ci_test":"positive self-checking testbench + negative RTL"},
    {"key":"vvp","category":"RTL simulation runtime","state":"EXECUTION_ADAPTER","ci_test":"testbench prints MQV_SIM_PASS"},
    {"key":"verilator","category":"RTL lint/simulation","state":"EXECUTION_ADAPTER","ci_test":"positive lint + deliberate undefined-signal failure"},
    {"key":"yosys","category":"synthesis/structural checks","state":"EXECUTION_ADAPTER","ci_test":"synthesis stats + deliberate undefined-signal failure"},
    {"key":"sby","category":"formal orchestration","state":"EXECUTION_ADAPTER","ci_test":"true property pass + false property counterexample"},
    {"key":"z3","category":"SMT solver","state":"SOLVER_ADAPTER","ci_test":"used by SymbiYosys regression tasks"},
    {"key":"boolector","category":"SMT solver","state":"SOLVER_DISCOVERY","ci_test":"runtime probe only unless selected in an explicit formal task"},
    {"key":"ghdl","category":"VHDL analysis/simulation","state":"EXECUTION_ADAPTER","ci_test":"valid VHDL pass + malformed VHDL rejection"},
    {"key":"opensta","category":"static timing analysis","state":"EXECUTION_ADAPTER","ci_test":"Liberty/netlist/SDC setup + deliberate timing violation"},
    {"key":"klayout","category":"layout/DRC","state":"EXECUTION_ADAPTER","ci_test":"generic positive/negative DRC smoke + separate official IHP activ golden table regression"},
    {"key":"OpenROAD","category":"physical design flow","state":"CATALOG_ONLY","ci_test":"dedicated flow adapter and PDK platform matrix remain future work"},
    {"key":"OpenLane / LibreLane","category":"RTL-to-GDS flow orchestration","state":"CATALOG_ONLY","ci_test":"platform-specific flow adapter and test fixture required"},
    {"key":"Magic","category":"layout/DRC/extraction","state":"CATALOG_ONLY","ci_test":"dedicated adapter and calibrated rule-deck regression pending"},
    {"key":"Netgen LVS","category":"layout-versus-schematic","state":"CATALOG_ONLY","ci_test":"dedicated adapter and known-good/known-bad LVS fixtures pending"},
    {"key":"OpenRCX","category":"parasitic extraction","state":"CATALOG_ONLY","ci_test":"OpenROAD component, not a separate executable adapter"},
    {"key":"Verible","category":"SystemVerilog lint/format","state":"RUNTIME_DISCOVERY","ci_test":"not in required execution regression yet"},
    {"key":"Surelog","category":"SystemVerilog parsing/elaboration","state":"RUNTIME_DISCOVERY","ci_test":"not in required execution regression yet"},
    {"key":"slang","category":"SystemVerilog parsing/semantic analysis","state":"RUNTIME_DISCOVERY","ci_test":"not in required execution regression yet"},
    {"key":"sv2v","category":"SystemVerilog-to-Verilog conversion","state":"RUNTIME_DISCOVERY","ci_test":"not in required execution regression yet"},
    {"key":"EQY","category":"equivalence checking","state":"RUNTIME_DISCOVERY","ci_test":"dedicated equivalence job required before validated status"},
    {"key":"Cocotb","category":"Python-based testbench framework","state":"CATALOG_ONLY","ci_test":"adapter to regression environment pending"},
    {"key":"NVC","category":"VHDL simulator","state":"CATALOG_ONLY","ci_test":"additional VHDL simulator adapter pending"},
    {"key":"GTKWave / Surfer","category":"waveform visualization","state":"CATALOG_ONLY","ci_test":"waveform artifact/viewer integration pending"},
    {"key":"ngspice","category":"SPICE circuit simulation","state":"CATALOG_ONLY","ci_test":"analog circuit workflow not in Session 1 validated scope"},
    {"key":"Xschem","category":"schematic editor","state":"CATALOG_ONLY","ci_test":"desktop application, not a headless verification adapter"},
    {"key":"Xyce","category":"SPICE simulation","state":"CATALOG_ONLY","ci_test":"analog circuit workflow not in Session 1 validated scope"},
    {"key":"openEMS","category":"electromagnetic simulation","state":"CATALOG_ONLY","ci_test":"separate domain integration; not a digital RTL check"},
    {"key":"CACE","category":"analog design automation","state":"CATALOG_ONLY","ci_test":"analog design workflow not in Session 1 validated scope"},
    {"key":"FuseSoC / Edalize","category":"build and tool-flow orchestration","state":"CATALOG_ONLY","ci_test":"manifest-driven project/build adapter pending"},
]
def list_tool_catalog() -> list[dict[str, str]]:
    return [dict(row) for row in TOOL_CATALOG]
