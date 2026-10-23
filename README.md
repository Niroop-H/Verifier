# MAH Quantum Verify — Session 1: EDA Verification

This repository is the reproducible engineering workspace for Session 1. It starts with a Linux CI/build foundation and acceptance tests; it does **not** claim that every EDA tool, PDK or sign-off flow is already integrated.

## Scope

- RTL lint, simulation and synthesis (Verilator, Icarus Verilog, Yosys)
- Formal workflows (SymbiYosys plus a configured solver)
- VHDL analysis (GHDL)
- Static timing (OpenSTA with real SDC and Liberty inputs)
- Physical verification (KLayout with user-authorized PDK rule decks)
- Reproducible evidence and explicit BLOCKED/NOT RUN semantics

## Build locally

See [docs/BUILD_LINUX.md](docs/BUILD_LINUX.md) for a clean Ubuntu build plan. CI runs smoke tests using system packages; full physical flows require PDK collateral and test fixtures.

## Result semantics

- `PASS`: the named check executed and met its stated criterion.
- `FAIL`: the named check executed and found a violation or returned a failing verdict.
- `BLOCKED`: a required tool, library, rule deck, or input is unavailable.
- `INCONCLUSIVE`: the run could not establish a verdict (timeout or unsupported result).
- `NOT RUN`: explicitly excluded by configuration.
- `ERROR`: infrastructure or adapter error; never reinterpret as PASS.

A passing smoke test is not foundry sign-off or fabrication readiness. No certification or universal-coverage claim is made.

## License and third-party tools

This repository orchestrates external tools; each tool and PDK keeps its own license and distribution conditions. Do not commit restricted foundry PDKs, licensed binaries, credentials, or classified/customer design data into this repository. Use authorized local paths or private artifact storage for such material.
