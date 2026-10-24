# Self-contained toolchain and source custody

## Objective

MAH Quantum Verify should build and execute from controlled, reviewed inputs without fetching source repositories during a customer verification run. The goal is reproducibility and source custody, not an arbitrary line-count target.

The manifest and source-vendor utility materialize selected upstream source files into `vendor/src/`, where the outer MAH Quantum Verify repository can track them as ordinary files. Large PDK/platform collateral is deliberately separated into optional packs instead of blindly copying multi-gigabyte technology data into the core product repository. Each snapshot retains upstream notices and has a provenance marker with its exact source URL, immutable commit SHA, and deterministic tree digest. This does **not** yet mean every EDA tool is vendored or that the platform is fully offline.

## Commands

From the repository root, with Git installed and network access for initial acquisition:

```bash
python scripts/vendor_sources.py status
python scripts/vendor_sources.py sync --pack formal
python scripts/vendor_sources.py verify --pack formal
python scripts/vendor_sources.py verify --name symbiyosys
```

A repository maintainer can also open **Actions → Vendor pinned EDA source snapshots → Run workflow**, select this branch, and type `VENDOR`. The workflow materializes and verifies every declared source snapshot, then commits the source files to the selected branch. Review the resulting source volume and license inventory before merging.

- `status` prints the pinned inputs. Use `--pack formal`, `--pack rtl-tooling`, or `--pack physical-design` to select a bounded source group; `--name NAME` remains available for a single dependency.
- `sync` clones the source at its exact full commit SHA and copies its tracked working tree into `vendor/src/`, excluding nested Git metadata. It preserves symlinks and original license/copyright files.
- `sync` refuses to overwrite a directory unless its provenance marker matches the expected source and revision and its current content digest is unchanged.
- `verify` validates source identity metadata and recomputes a deterministic SHA-256 digest over all source paths, file contents, executable bits, and symlink targets. Any content change is detected.
- `verify` also checks SHA-256 for any declared binary artifact acquired into its declared location.

Once source snapshots have been synchronized and committed to this repository, ordinary product runtime must not call this utility or fetch upstream code. The vendored source files are then present in the outer repository history and survive deletion of an upstream repository, subject to Git hosting limits and normal repository backup practices.

## Current pinned inputs

The manifest pins 16 source repositories and records an OSS CAD Suite release archive and checksum. Source groups are `formal` (SymbiYosys, EQY, Z3, Boolector), `rtl-tooling` (Yosys, Icarus Verilog, Verilator, GHDL, Verible, Surelog, sv2v, cocotb), and `physical-design` (OpenROAD, OpenSTA, OpenROAD-flow-scripts, OpenLane). These are acquisition groupings, not guarantees of completeness or production readiness. PDK/platform collateral remains separately versioned. The utility does not download the binary artifact automatically.

## Required next stages

1. **Inventory every dependency.** Include executables, Python packages, build tools, libraries, test fixtures, CI downloads, PDK collateral, Liberty files, rule decks, container base images, and generated artifacts.
2. **Pin everything.** Use immutable Git commit IDs or versioned release artifacts with cryptographic hashes. A tag or branch alone is not an immutable pin.
3. **Resolve license and redistribution rights.** Preserve copyright, attribution, and license files. Review dependencies transitively; a permissive top-level project does not automatically make every dependency permissive.
4. **Materialize and commit the actual source trees.** Run the sync utility in a controlled clone, review the resulting diff and repository size, then commit the source files through the approved PR workflow. The manual import workflow processes one selected source pack at a time, measures that pack's volume, and refuses oversized files or a pack exceeding 1.5 GiB. Run it from Actions → Vendor pinned EDA source snapshots, choose a pack, and type `VENDOR`. It no longer automatically attempts to import all 16 repositories on every push. If a tool contains bulky PDKs, libraries, or generated collateral, those must be separately pinned and reviewed as optional packs rather than forcing the whole payload into one Git repository.
5. **Build from a clean network-disabled environment.** Use a staged dependency cache or approved source archive. Product runtime must not invoke Git, curl, wget, or package managers to fetch missing tools.
6. **Create reproducible toolchain images.** Pin OS/container images by digest, record compiler/build flags, and produce a software bill of materials and provenance record.
7. **Separate proprietary product code from upstream components.** Keep original MAH Quantum modules, interfaces, algorithms, UX, evidence engine, and orchestration clearly identified. Do not strip or replace third-party notices.
8. **Validate each flow against known fixtures.** A bundled tool is not automatically a validated tool. Record versions, expected results, failure fixtures, and known limitations.
9. **Define a customer redistribution policy.** Some source, binary, PDK, and foundry collateral may be usable internally but not redistributable to customers.

## Intellectual property boundaries

MAH Quantum can retain proprietary rights in independently authored code, product-specific modifications where the applicable license permits, build and deployment automation, and original product assets. Third-party components remain governed by their original licenses. Do not describe upstream source as exclusively MAH Quantum-owned or remove notices in an attempt to make it proprietary.

## Scope limitation

This is an engineering foundation, not a completed million-line integration. The manifest currently declares 16 source repositories and one binary toolchain artifact. The utility does not yet recursively resolve every dependency, authenticate Git commit signatures, audit license compatibility, or prove reproducible builds. Those remain acceptance criteria.
