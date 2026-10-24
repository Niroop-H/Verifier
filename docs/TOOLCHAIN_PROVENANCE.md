# Toolchain provenance and licensing

The CI job uses Ubuntu packages for some open-source tools and records their runtime version output in the evidence artifact. SymbiYosys is checked out at commit 79fc9eddca5e33a28cc2f2cd19c9825efd9a7255. KLayout is installed from the vendor's Ubuntu package at version 0.30.10; the download is checked against a vendor-published checksum (integrity checking only, not a cryptographic authenticity guarantee).

The STA regression downloads the Nangate45 typical Liberty library from OpenROAD-flow-scripts commit eda8e552974d47a12616294dddf4012d892548d3 at test time. The library is used only for a synthetic timing regression and is not redistributed by this repository. Review its upstream terms before reuse.

The self-contained toolchain plan is documented in [SELF_CONTAINED_TOOLCHAIN.md](SELF_CONTAINED_TOOLCHAIN.md), with initial pinned source inputs in [vendor/manifest.json](../vendor/manifest.json). The source-vendor utility is `scripts/vendor_sources.py`.

Do not treat package names as version pins. The artifacts produced by each run are the record of actual package and executable versions. A source pin is not license approval, and a vendored source repository does not imply that its PDKs, libraries, rule decks, or build dependencies can be redistributed.
