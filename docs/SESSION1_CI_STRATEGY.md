# Session 1 CI strategy

## Why a pinned tool suite

The CI build installs the official YosysHQ OSS CAD Suite release for Linux x86-64 (release 2026-10-22) after checking the published SHA-256 digest. It provides a mutually compatible baseline for Icarus Verilog, Verilator, Yosys, GHDL, SymbiYosys and supported formal solvers. KLayout is installed from its official Ubuntu 24 package with a checksum check. OpenSTA is separately built from a pinned source commit because it is not part of the suite's documented tool list.

## Release evidence

The workflow must archive:
- test log and JUnit XML,
- toolchain discovery output,
- commit hash,
- source package.

A green core smoke-test run validates only the included regression fixtures. It does not validate every EDA adapter or every PDK. Physical PDK flows need separate follow-on tests with explicitly identified decks, PDK revisions and positive/negative test layouts.

## Security note

Never put private or NDA-restricted foundry collateral or customer design data in a public repository. Tool scripts and uploaded HDL can be executable inputs: production execution must occur in isolated workers with explicit time, CPU, memory, disk and network policies.
