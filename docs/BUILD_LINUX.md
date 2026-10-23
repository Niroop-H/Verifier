# Linux build and validation guide

## Recommended baseline
Use Ubuntu 24.04 x86-64. Build in a fresh VM/container; don't install tools on the desktop merely to run CI. This build uses distro packages first for repeatability, with source builds added only when an available distro package fails the version/capability gate.

## Bootstrap
```bash
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  build-essential cmake ninja-build git curl ca-certificates pkg-config \
  python3 python3-pip python3-venv python3-dev \
  iverilog verilator yosys ghdl z3 boolector \
  klayout opensta
```
Package names and versions can differ between Ubuntu releases. The workflow records actual tool versions and marks a check BLOCKED if the executable or required collateral is not present. Do not silently count BLOCKED as PASS.

## Python test environment
```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
pytest -q -rs
```

## Tools supplied as source archives
Icarus, Verilator, Yosys, GHDL, OpenSTA, SymbiYosys, Boolector and Z3 are independent projects. Source archives are not executable programs. Build each against the target OS/toolchain using that project's official instructions; pin a release or commit and record the exact revision. Don't use arbitrary `master` archives for a release build.

## PDK setup
Keep PDKs outside the application repository, e.g. under `/opt/pdks`. Set:
- `MAHQV_TEST_IHP_PDK=/opt/pdks/IHP-Open-PDK`
- `MAHQV_TEST_GF180_PDK=/opt/pdks/gf180mcu-pdk`
- `MAHQV_TEST_SKY130_PDK=/opt/pdks/skywater-pdk`

Preserve the official repo's submodules and install steps; source ZIPs often omit submodule contents. Before enabling a PDK profile, verify its libraries, model files, layer map, DRC/LVS decks, and license/redistribution terms.

## Acceptance rule
For each capability, preserve command, tool version, input hash, exit code, normalized result, raw log location, and any missing prerequisite. Run both known-good and known-bad fixtures. For formal verification distinguish bounded model checking from an unbounded proof. For STA, require an actual netlist, SDC, and compatible Liberty library. A PDK profile is not sign-off merely because its JSON exists.
