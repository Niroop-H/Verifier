# Self-contained toolchain and source custody

## Objective

MAH Quantum Verify should be able to build and execute from controlled, reviewed inputs without fetching source repositories during a customer verification run. The goal is reproducibility and source custody, not an arbitrary line-count target.

This first increment adds a manifest and a deterministic source-vendor utility. It does **not** yet claim that every EDA tool is vendored, that all transitive dependencies are captured, or that the platform is fully offline. The listed source snapshots are the starting set; every additional dependency must be added after its exact revision, license, build instructions, and transitive dependencies are reviewed.

## Commands

From the repository root, with Git installed:

```bash
python scripts/vendor_sources.py status
python scripts/vendor_sources.py sync
python scripts/vendor_sources.py verify
python scripts/vendor_sources.py verify --name symbiyosys
```

- `status` prints the declared pinned inputs.
- `sync` checks out full immutable Git commit IDs into `vendor/src/`. It refuses to overwrite a dirty checkout or a directory that is not already a Git repository.
- `verify` confirms origin, exact commit, and clean working tree. It also checks SHA-256 for any declared binary artifact that has been acquired into its declared location.

Source repositories retain their own Git metadata and history. They are not copied into MAH Quantum's Python package and are not silently rewritten or renamed. For a source release that must be archived as plain files rather than Git repositories, create a separately reviewed source archive with a recorded hash and keep the original license files.

## Current pinned inputs

The manifest uses revisions already present in the repository's toolchain provenance and CI configuration. This reduces guesswork but is not a substitute for revalidating each upstream repository and release before customer distribution.

The OSS CAD Suite entry records a release archive and SHA-256 used by existing CI. The utility does not download this binary artifact automatically: acquisition, platform compatibility, license review, and redistribution approval must happen before bundling it into an installer.

## Required next stages

1. **Inventory all runtime dependencies.** Include executables, Python packages, build tools, libraries, test fixtures, CI downloads, PDK collateral, Liberty files, rule decks, container base images, and generated artifacts.
2. **Pin everything.** Use immutable Git commit IDs or versioned release artifacts with cryptographic hashes. A tag or branch alone is not an immutable pin.
3. **Resolve license and redistribution rights.** Preserve copyright, attribution, and license files. Review dependencies transitively; a permissive top-level project does not automatically make every dependency permissive.
4. **Build from a clean network-disabled environment.** Use a staged dependency cache or approved source archive. The product runtime must not invoke Git, curl, wget, or package managers to fetch missing tools.
5. **Create reproducible toolchain images.** Pin OS/container images by digest, record compiler/build flags, and produce a bill of materials and provenance record.
6. **Separate proprietary product code from upstream components.** Keep original MAH Quantum modules, interfaces, algorithms, UX, evidence engine, and orchestration clearly identified. Do not strip or replace third-party notices.
7. **Validate each flow against known fixtures.** A bundled tool is not automatically a validated tool. Record versions, expected results, failure fixtures, and known limitations.
8. **Define a customer redistribution policy.** Some source, binary, PDK, and foundry collateral may be usable internally but not redistributable to customers.

## Intellectual property boundaries

MAH Quantum can retain proprietary rights in its independently authored code, product-specific modifications where the applicable license permits, build and deployment automation, and original product assets. Third-party components remain governed by their original licenses. Do not describe upstream source as exclusively MAH Quantum-owned or remove notices in an attempt to make it proprietary.

## Scope limitation

This is an engineering foundation, not a completed million-line integration. The initial manifest contains three source repositories and one recorded binary toolchain artifact. The utility verifies declared source snapshots; it does not yet recursively resolve every dependency, authenticate Git commit signatures, audit license compatibility, or prove reproducible builds. Those remain explicit acceptance criteria.
