# Open PDK integration policy

- Keep PDKs out of the application repo and CI artifacts unless the PDK license expressly allows that distribution.
- Never bundle customer/foundry collateral or secrets in a public repository.
- An enabled profile must pin/identify the process release, libraries, layer map, DRC/LVS decks, model files where applicable, and required tool versions.
- Public PDK presence does not imply foundry sign-off. Predictive PDKs such as ASAP7 are research platforms, not production foundry-qualified processes.
- CI can use synthetic fixtures for generic checks. PDK-backed DRC/LVS tests run only when the exact PDK/deck is present and versioned; otherwise they report BLOCKED with the prerequisite.
