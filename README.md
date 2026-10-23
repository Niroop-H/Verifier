# MAH Quantum Verify — Session 1: EDA Verification

This repository is the Session 1 engineering workspace. It provides a local Python orchestration core, Linux toolchain CI, reproducible regression fixtures, and structured evidence reports. It is a pre-release engineering build.

## Implemented in this repository
- Safe ZIP extraction with path traversal, symlink, size, file-count and compression-ratio controls.
- Runtime discovery of Icarus/VVP, Verilator, Yosys, GHDL, SymbiYosys, Z3, Boolector, KLayout and OpenSTA.
- RTL lint, compile and Yosys synthesis adapters.
- Optional testbench compile/run, VHDL analysis, user-supplied SBY tasks, OpenSTA with netlist+Liberty+SDC, and parameterized KLayout DRC/LVS deck adapters.
- Fail-closed result semantics: PASS, FAIL, BLOCKED, INCONCLUSIVE, NOT RUN, ERROR.
- SHA-256 input inventory, tool versions, raw logs, JSON report and HTML report.
- GitHub Actions build and tool-backed smoke regressions.

## Quick start
    python3 -m pip install -r requirements-dev.txt
    python -m mqv_eda doctor
    python -m mqv_eda verify fixtures/rtl/comb.v --top comb --out build/demo

For Linux dependencies and full regression instructions see docs/BUILD_LINUX.md.
Acceptance criteria are in docs/SESSION1_ACCEPTANCE.md.

## Result semantics
- PASS: the named executable check ran and met its stated criterion.
- FAIL: the check ran and exposed a violation or invalid input.
- BLOCKED: a required tool, input, library, deck or prerequisite is missing.
- INCONCLUSIVE: a timeout or output that cannot be interpreted reliably.
- NOT RUN: intentionally not executed because the relevant input or option was not supplied.
- ERROR: adapter or infrastructure error. ERROR is never reinterpreted as PASS.

## Boundaries
A generic EDA orchestrator is not a substitute for all proprietary sign-off tools. The included KLayout adapter only supports decks conforming to its documented input_file/report_file interface. No certification, foundry qualification, defence approval, universal coverage or fabrication-readiness claim is made.
