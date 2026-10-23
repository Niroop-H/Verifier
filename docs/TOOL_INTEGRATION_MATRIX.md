# EDA tool integration matrix

The catalogue is broader than the set of adapters tested in CI. Do not use catalogue presence as a claim of executable integration.

| Tool / ecosystem | State | Actual scope |
|---|---|---|
| Icarus Verilog + VVP | Execution adapter, CI exercised | RTL compile and self-checking testbench; faulty RTL rejected. |
| Verilator | Execution adapter, CI exercised | RTL lint on good and bad fixtures. Not a replacement for formal or simulation coverage. |
| Yosys | Execution adapter, CI exercised | Hierarchy, process lowering, structural checks and synthesis reports. |
| SymbiYosys + Z3 | Formal adapter, CI exercised | User-authored tasks; true property passes and false property produces a counterexample. |
| GHDL | VHDL adapter, CI exercised | Valid and invalid VHDL fixtures; functional tests require supplied testbenches. |
| OpenSTA | Timing adapter, CI exercised | Gate-level netlist + Liberty + SDC; both timing pass and a deliberate violation are checked using a synthetic test library. Not sign-off timing. |
| KLayout | Layout adapter, CI exercised | Generic synthetic DRC smoke plus official IHP activ-table golden comparison. Generic adapter is not interchangeable with every foundry deck. |
| Boolector | Solver discovery | Specific job configuration and a dedicated proof regression are required before selecting it by default. |
| OpenROAD, OpenLane, LibreLane | Catalogue / future adapters | Full RTL-to-GDS flow requires a pinned platform, flow scripts, PDK collateral, resource profiles and regression fixtures. |
| Magic, Netgen LVS, OpenRCX | Catalogue / future adapters | Dedicated extraction, DRC/LVS, parasitic-extraction adapters and positive/negative fixtures remain required. |
| Verible, Surelog, slang, sv2v, EQY | Optional tool discovery / catalogue | Additional parsing, linting, conversion and equivalence workflows need named adapters and regression evidence. |
| Cocotb, NVC, GTKWave, Surfer | Catalogue | Testbench integration, additional VHDL simulation and waveform view/export are not complete merely because projects exist. |
| ngspice, Xschem, Xyce, openEMS, CACE | Catalogue | Analog/EM workflows are separate integration domains, outside the currently validated RTL core. |
| FuseSoC / Edalize | Catalogue | Manifest-driven project/build orchestration adapter remains planned. |

A tool is marked execution adapter only if MAH Quantum Verify contains an execution path for it. The doctor command reports executable presence/version; it does not by itself mark a flow validated.
