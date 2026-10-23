# Open PDK integration policy

- PDKs live outside this public application repository and its normal CI artifacts unless the exact license expressly permits redistribution.
- Never commit customer design data, credentials, restricted foundry collateral, or commercial tool binaries.
- An enabled profile records process release, libraries, layer maps, DRC/LVS deck revisions, tool versions, required environment variables and license terms.
- A predictive/academic PDK does not imply production foundry qualification.
- A physical check must preserve the raw tool report and parser status. If a deck runs but does not produce a recognizable report, result is INCONCLUSIVE, not PASS.
- Generic DRC/LVS command adapters are not interchangeable with every foundry's deck flow; deck-specific integration and regression fixtures are required.
