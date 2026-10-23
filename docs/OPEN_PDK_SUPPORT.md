# PDK and platform readiness

This project distinguishes source/profile catalogue from actual physical-flow validation.

| Profile | Type | Current state in this release |
|---|---|---|
| SKY130 | Open PDK ecosystem (experimental-preview) | Catalogue and root-marker inspection; physical integration depends on a compatible Open PDKs/OpenROAD platform and initialized submodules. |
| SKY130 HD | Standard-cell library option within SKY130 | Separate library profile; not a separate process node. |
| GF180MCU | Open PDK ecosystem (experimental-preview) | Catalogue/root-marker inspection; submodules and a compatible DRC/LVS deck setup are required. |
| IHP SG13G2 | 130 nm BiCMOS open PDK | CI includes the official IHP DRC golden regression for the activ rule table. This is partial evidence for one table only; all-rule DRC, LVS and full sign-off are not claimed. |
| ASAP7 | Predictive research platform | Catalogue only; not a foundry-qualified 7 nm production PDK. Some commercial sign-off collateral is separately distributed. |
| Nangate45 / FreePDK45 | Educational timing test platform | Used as a synthetic STA test-library source only; not a commercial foundry platform. |
| Generic OpenROAD | Flow backend | Not a PDK. A separate technology platform, library and rule decks are required. |

## Local inspection

    python -m mqv_eda pdks
    python -m mqv_eda pdks --profile ihp_sg13g2 --root /opt/pdks/IHP-Open-PDK --json

The second command only checks file paths and Liberty files. A root marker is not a functional result. Before a flow is enabled, preserve the exact PDK commit, tool/deck versions, layer maps, positive and negative designs, raw logs and parsed DRC/LVS output.

Official source repositories:
- SKY130: https://github.com/google/skywater-pdk
- GF180MCU: https://github.com/google/gf180mcu-pdk
- IHP SG13G2: https://github.com/IHP-GmbH/IHP-Open-PDK
- ASAP7: https://github.com/The-OpenROAD-Project/asap7
- OpenROAD platforms: https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts

Restricted/commercial technology kits are not described as open PDKs here. Authorized customer collateral can be used only with the required permissions and deployment approvals.
