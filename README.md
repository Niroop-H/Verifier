# MAH Quantum Verify — Session 1: EDA Verification

This repository is the current Session 1 engineering workspace. It provides a local Python execution core, a reproducible Linux EDA toolchain in GitHub Actions, regression fixtures, PDK readiness inspection, tool integration status, and structured evidence reports.

## Quick start

    python3 -m pip install -r requirements-dev.txt
    python -m mqv_eda doctor
    python -m mqv_eda tool-catalog
    python -m mqv_eda pdks
    python -m mqv_eda verify fixtures/projects/good --top comb --testbench tb_comb.v --sim-top tb_comb --out build/demo

## Implemented execution adapters

- Safe ZIP extraction with traversal, symlink, special-file, size, entry-count and compression-ratio controls.
- Runtime tool discovery including Icarus/VVP, Verilator, Yosys, GHDL, SymbiYosys, Z3, Boolector, KLayout, OpenSTA and optional ecosystem tools.
- RTL lint, compile, testbench compile/run, Yosys synthesis and structural checks.
- User-supplied SymbiYosys tasks with explicit formal verdicts.
- VHDL analysis.
- OpenSTA timing via a real gate-level netlist, Liberty library and SDC inputs.
- KLayout deck adapter with an explicit report-file contract, generic positive/negative DRC smoke fixture, and separate official IHP SG13G2 Activ-table golden regression in CI.
- Fail-closed statuses: PASS, FAIL, BLOCKED, INCONCLUSIVE, NOT RUN, ERROR.
- SHA-256 input inventory, tool versions, raw logs, JSON and HTML evidence reports.
- Local PDK collateral inspection and integration-state catalog.

## PDK and tool status

The PDK catalogue includes SKY130, SKY130 HD, GF180MCU, IHP SG13G2, ASAP7, Nangate45 test-platform files and the generic OpenROAD backend. A source repo or PDK profile does not equal validated DRC/LVS. See docs/OPEN_PDK_SUPPORT.md.

The tool catalogue includes common open EDA tools, explicitly distinguishing execution adapters from catalogue-only and runtime-discovery entries. See docs/TOOL_INTEGRATION_MATRIX.md.

## Build, validation and boundaries

Follow docs/BUILD_LINUX.md. CI artifacts include the tool manifest, regression logs, reports and official IHP DRC golden output. See docs/SESSION1_ACCEPTANCE.md for release gates and docs/TOOLCHAIN_PROVENANCE.md for tool sources.

A PASS only applies to the specific check and inputs. This repository does not claim universal chip verification, foundry qualification, sign-off timing, defence certification, or fabrication-readiness approval. Restricted foundry collateral and commercial tools must only be used with appropriate authorization and licensing.
