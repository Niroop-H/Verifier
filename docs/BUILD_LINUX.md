# Reproducible Linux build (Session 1)

The primary CI target is Ubuntu 24.04 x86-64. Use a disposable, isolated build runner. Never execute untrusted RTL, formal-task files, timing Tcl scripts, KLayout decks or customer content on a privileged host.

## Required tools

Python 3.12 and pytest, Icarus Verilog (iverilog and vvp), Verilator, Yosys, GHDL, Z3, SymbiYosys (sby), OpenSTA (sta), and KLayout 0.30.5 or newer.

The GitHub Actions workflow installs the system toolchain, pins SymbiYosys/OpenSTA source revisions, installs a versioned KLayout package with checksum verification, runs tool-driven smoke tests, and uploads tool versions and logs.

## Local setup

Use the commands in .github/workflows/session1-ci.yml as the source of truth for CI.

    python3 -m venv .venv
    . .venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install -e '.[test]'
    pytest -q -rs
    mqv-eda doctor --json

## CLI

    mqv-eda doctor --json
    mqv-eda lint --top alu examples/rtl/alu.sv
    mqv-eda simulate --top tb examples/rtl/alu.sv examples/rtl/tb.sv
    mqv-eda synth --top alu examples/rtl/alu.sv
    mqv-eda vhdl --top logic examples/vhdl/logic.vhd
    mqv-eda formal /absolute/path/to/authorized_task.sby
    mqv-eda timing /absolute/path/to/authorized_timing.tcl
    mqv-eda drc --deck /absolute/path/to/authorized_deck.drc --layout /absolute/path/to/design.gds

Formal, timing and layout decks can execute code. Use only authorized decks in an isolated worker with CPU, memory, disk and runtime quotas.
