# Linux build and test guide

## Supported build runner
The CI reference runner is Ubuntu 22.04 x86-64 because it provides a consistent baseline for this first open-source EDA suite. Package versions are captured in the job artifact. Use a container or VM for local reproduction.

## Install core tools
Run from a clean Ubuntu machine:
    
    sudo apt-get update
    sudo apt-get install -y build-essential cmake git curl ca-certificates python3 python3-pip python3-venv \
      iverilog verilator yosys ghdl z3 boolector klayout opensta

SymbiYosys (sby) is installed at an explicitly pinned upstream commit by CI:
    
    git clone https://github.com/YosysHQ/sby.git
    cd sby
    git checkout 79fc9eddca5e33a28cc2f2cd19c9825efd9a7255
    sudo make install PREFIX=/usr/local

Package availability varies by distribution. Always check the tool manifest after installation.

## Run project tests
    python3 -m venv .venv
    . .venv/bin/activate
    python -m pip install -r requirements-dev.txt
    python -m pytest -q -rs
    bash scripts/run_regressions.sh

## Run the local verification engine
    python -m mqv_eda doctor
    python -m mqv_eda verify fixtures/rtl/comb.v --top comb --out build/demo

For a design with a testbench:
    python -m mqv_eda verify path/to/project.zip --top my_top --testbench tb/tb_my_top.sv --sim-top tb_my_top --out build/my_run

For STA provide a gate-level Verilog netlist, a Liberty timing library and SDC:
    python -m mqv_eda verify project/ --top my_top --netlist build/netlist.v --liberty platform/cells.lib --sdc constraints.sdc

For physical checks, supply an authorized deck and GDSII. The generic deck adapter uses input_file and report_file; only decks designed for this interface should be passed to it. Profile-specific decks may need a dedicated adapter.

The engine runs local commands and emits JSON/HTML evidence. It does not upload design sources. Verify customer and foundry data-handling requirements before using any hosted CI worker.
