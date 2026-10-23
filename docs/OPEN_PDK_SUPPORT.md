# Open PDK and physical-flow support

MAH Quantum Verify treats PDK discovery separately from DRC/LVS validation. A PDK profile may identify a public source repository, but that alone does not guarantee compatible cell libraries, layer maps, rule decks, submodules or a successful layout test.

## Catalogue

| Profile | Public source | State in this repository |
|---|---|---|
| SKY130 | https://github.com/google/skywater-pdk | Catalogue/profile; compatible platform and external deck setup must be checked |
| SKY130 HD | https://github.com/google/skywater-pdk | Standard-cell library option within SKY130; not a separate process |
| GF180MCU | https://github.com/google/gf180mcu-pdk | Catalogue/profile; repository uses submodules and is an experimental preview |
| IHP SG13G2 | https://github.com/IHP-GmbH/IHP-Open-PDK | Expected DRC/LVS deck paths registered; require deck execution and regression evidence |
| ASAP7 | https://github.com/The-OpenROAD-Project/asap7 | Predictive research platform; proprietary Calibre decks are separate |
| Generic OpenROAD | https://github.com/The-OpenROAD-Project/OpenROAD | Backend only, not a PDK |

## Readiness requirement

A PDK may be marked validated only after recording the PDK commit/release, submodule state, exact deck paths and versions, layer map, library corner, real good/bad layout fixtures, DRC/LVS logs, and reproducible outputs. A synthetic KLayout smoke test only validates the KLayout runtime; it is not foundry DRC.

## Command

Use the Python API now exposed by the engine:

    from mahqv_eda.pdks import inspect_profile
    print(inspect_profile("ihp_sg13g2", "/path/to/IHP-Open-PDK"))

The result returns missing markers and deck blockers rather than silently treating a directory as supported.
