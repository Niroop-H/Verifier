# Session 1 EDA acceptance criteria

This is a release gate, not a declaration that every item has already passed.

## Required core flows
1. RTL lint with Verilator on clean and defective designs.
2. Icarus compilation and execution of a self-checking testbench.
3. Yosys hierarchy, process lowering, optimization, structural checks, and synthesis statistics.
4. GHDL analysis of valid VHDL and rejection of intentionally invalid VHDL.
5. SymbiYosys with Z3 proves a valid assertion and finds a counterexample for a deliberately false assertion.
6. OpenSTA loads a gate-level netlist, a real Liberty library, and SDC constraints, then reports path slack. Version-only probing does not satisfy this gate.
7. KLayout executes a DRC deck using documented input/report parameters and result parser. A successful process exit alone does not prove zero violations.
8. Required BLOCKED, NOT RUN, ERROR and INCONCLUSIVE checks never aggregate to PASS.
9. JSON/HTML evidence contains command, tool version, input hashes, exit status, log, and explicit limitations.
10. A clean Linux runner can repeat the test suite from the repository.

## PDK-specific gate
A PDK profile is enabled for physical checking only when the process release, layer maps, technology libraries, model files where required, DRC/LVS deck paths, tool versions and license/redistribution terms are identified. Otherwise report BLOCKED. Predictive PDKs are research flows, not foundry sign-off.

## Completion decision
Close Session 1 only after the CI evidence for core RTL, simulation, synthesis, formal, VHDL and real timing is green. DRC/LVS results are separate and may remain BLOCKED until authorized PDK collateral and a validated deck adapter are configured. A green generic suite is not sign-off or fabrication readiness.
