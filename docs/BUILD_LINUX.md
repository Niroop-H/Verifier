# Linux build and test guide

## Reference environment

Use Ubuntu 24.04 x86-64. A clean VM or CI runner is preferred. The CI workflow installs the pinned OSS CAD Suite release, KLayout 0.30.10 and builds OpenSTA against CUDD. CI output records actual executable versions.

## Local prerequisites

    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv

Install core open-source EDA executables using the project's official instructions or the matching OSS CAD Suite release. For KLayout use https://www.klayout.de/build.html. Do not use Windows binaries inside Linux CI.

## Python environment

    python3 -m venv .venv
    . .venv/bin/activate
    python -m pip install -r requirements-dev.txt
    python -m pytest -q -rs

## Diagnose tools and profiles

    python -m mqv_eda doctor
    python -m mqv_eda tool-catalog
    python -m mqv_eda pdks
    python -m mqv_eda pdks --profile ihp_sg13g2 --root /opt/pdks/IHP-Open-PDK --json

The PDK command inspects expected files only. It does not validate deck execution or foundry sign-off.

## Run RTL verification

    python -m mqv_eda verify fixtures/projects/good --top comb --testbench tb_comb.v --sim-top tb_comb --out build/demo

For static timing, provide a gate-level netlist, compatible Liberty, and SDC:

    python -m mqv_eda verify project/ --top my_top --netlist build/netlist.v --liberty platform/cells.lib --sdc constraints.sdc

For physical DRC/LVS, provide an authorized deck and the actual GDS/reference netlist. The generic KLayout adapter expects a deck that consumes input_file and report_file (and netlist_file for the configured LVS call). Foundry scripts with other interfaces need dedicated adapters.

## Evidence manifest and integrity verification

Each verification run writes `evidence-manifest.json` alongside the JSON and HTML reports. To verify referenced files:

```bash
python -m mqv_eda verify fixtures/projects/good --top comb --testbench tb_comb.v --sim-top tb_comb --out build/demo --bundle-inputs
python -m mqv_eda verify-evidence build/demo/evidence-manifest.json
```

External design inputs are not copied by default. `--bundle-inputs` opts into copying known external inputs into the evidence directory, with a default 100 MiB cap. Adjust with `--max-bundle-mb N`. Only bundle RTL, libraries, netlists, PDK collateral, or rule decks when you are authorized to retain and distribute them. A passing integrity check confirms referenced bytes match recorded hashes; it does not prove design correctness, a signature, foundry sign-off, or fabrication readiness. See [Evidence Manifest](EVIDENCE_MANIFEST.md).

## Results and status

- PASS: the named check ran and met the stated criterion.
- FAIL: the check ran and reported a violation or invalid input.
- BLOCKED: a required tool, file, library, deck or version is missing.
- INCONCLUSIVE: timeout or unclear report prevents a verdict.
- NOT RUN: no relevant input or option was supplied.
- ERROR: adapter or infrastructure error.

Required BLOCKED/NOT RUN/ERROR must never be summarized as PASS. OpenSTA results depend on the specific libraries and constraints. A generic DRC smoke is not a foundry rules regression.
