# Feature implementation status

Updated: 2026-10-24

This tracker separates code that exists from complete acceptance of the original 50-feature roadmap. “Partial” means useful implementation exists, but one or more stated acceptance criteria, integration, deployment controls, or validation steps remain. “Implemented baseline” does not mean production-ready, certified, or safe for every customer environment.

## Current count

- **19 implemented baselines**
- **31 partial implementations**
- **0 completely unimplemented items currently tracked**
- Therefore, **31 of 50 still need work to meet their full acceptance criteria**. Partial items are not starting from zero.

## Item-by-item status

| # | Feature | Status | Remaining work |
|---:|---|---|---|
| 1 | Immutable run identity | Partial | Run identity is now attached to each standard verification report and local worker report, bound to input/config/toolchain fingerprints; immutable external storage and end-of-run lifecycle linkage remain |
| 2 | Complete input inventory | Partial | Capture transitive includes, policy-approved environment and untracked inputs at job start |
| 3 | Toolchain identity snapshot | Partial | Standard verification and worker reports now embed tool discovery/version output and missing-tool state; executable digests, signed tool identity, and pinned adapter provenance remain |
| 4 | Reproducible-run comparison | Partial | Execute controlled reruns and classify expected nondeterminism |
| 5 | Evidence bundle manifest verification | Implemented baseline | Continue adversarial archive testing and release hardening |
| 6 | Detached evidence signatures | Implemented baseline | Production trust-root and key lifecycle integration remains deployment-specific |
| 7 | Evidence retention policy | Partial | Guarded file-level archive/delete actions now support dry-run, archive digest verification, and explicit digest confirmation for deletion; scheduled retention, immutable audit storage, directory/archive policy, and legal controls remain |
| 8 | Portable evidence export | Implemented baseline | Expand interoperable schemas as more reports are supported |
| 9 | Evidence completeness scorecard | Implemented baseline | Integrate expected evidence profiles with actual run policies |
| 10 | Run provenance chain | Partial | Standard verify and local worker now emit a provenance JSON linking run identity to the report hash; detached signing, bundle linkage, durable provenance storage and trust verification remain |
| 11 | Verification policy engine | Implemented baseline | Integrate policy evaluation into authenticated release workflows |
| 12 | Fail-closed missing-evidence behavior | Implemented baseline | Add broader integration and adversarial regression coverage |
| 13 | Policy versioning | Implemented baseline | Add managed immutable policy storage and migration lifecycle |
| 14 | Human approval gate | Partial | Authenticated identities, durable approvals and protected storage |
| 15 | Separation of duties | Partial | Enforce in a trusted service; current local helper is not an identity system |
| 16 | Waiver and exception register | Partial | SQLite-backed scoped records, expiry, revocation and event history now exist; authenticated authorization, review workflow, protected storage and multi-user service integration remain |
| 17 | Policy dry-run mode | Implemented baseline | Expand policy-specific preview coverage |
| 18 | Baseline freshness rules | Partial | Fail-closed CLI gate now checks baseline run timestamp, max age, and source revision equality; policy-driven rerun execution and baseline approval workflow remain |
| 19 | Change-impact rule mapping | Partial | Dependency-aware mappings and explicit integration with skipped checks |
| 20 | Decision explanation report | Implemented baseline | Add richer HTML rendering and integration |
| 21 | Regression history and trend view | Partial | Persistent run store and trend visualizations |
| 22 | Changed-check detection | Implemented baseline | Add more input and requirement-change cases |
| 23 | Failure clustering | Implemented baseline | Tune against real logs and preserve links to source artifacts |
| 24 | Deterministic log triage | Implemented baseline | Broaden fixture coverage and adapter-specific patterns |
| 25 | Flaky-test detector | Implemented baseline | Add repeat orchestration and enforce identical-input/toolchain controls |
| 26 | Mutation-test benchmark | Partial | Execute curated RTL mutants through real tools; metrics helper alone is not a runner |
| 27 | False-pass / false-failure metrics | Partial | Establish reviewed benchmark corpus and statistically defensible methodology |
| 28 | Coverage trend ingestion | Partial | Add toggle/functional formats and persistent trends beyond Cobertura-style XML |
| 29 | Regression minimization | Partial | Rerun selected subsets and prove failure reproduction in supported runners |
| 30 | Golden-corpus versioning | Implemented baseline | Add required review workflow for expected-outcome changes |
| 31 | Worker isolation contract | Partial | Host-specific adversarial tests, resource event capture and deployment validation |
| 32 | No-network execution mode | Partial | Docker runner requests --network=none; validate all supported deployment paths |
| 33 | Workspace path containment | Implemented baseline | Continue TOCTOU and platform-specific path testing |
| 34 | Secret-safe logging | Implemented baseline | Add more secret formats and test all report/log sinks |
| 35 | Dependency inventory / SBOM | Partial | SBOM now includes installed Python distributions plus native EDA tool PATH presence and declared integration tiers; binary digests/versions, OS packages, PDK metadata, licensing validation, and official schema validation remain |
| 36 | License and notice inventory | Partial | CLI inventories license/notice-like files, hashes them, extracts explicit SPDX tags, and flags manual-review files; complete source coverage, dependency mapping, compatibility checks and legal review remain |
| 37 | Signed build provenance | Partial | Bind build artifacts to builder identity and signed provenance/trust roots |
| 38 | Customer-managed worker mode | Partial | Complete control-plane/worker separation and prove RTL never leaves the customer host |
| 39 | Role and action audit | Implemented baseline | Protect storage and connect authenticated actors in deployed services |
| 40 | Incident-ready execution record | Partial | Persist termination causes, resource-limit events and worker identity |
| 41 | Stable CLI contract | Partial | Normalize legacy output envelopes and lock down every exit code in tests |
| 42 | API schema and compatibility policy | Partial | Reference OpenAPI contract exists; an authenticated API server is not implemented |
| 43 | Queue and cancellation semantics | Partial | SQLite-backed local lifecycle, atomic claim, event history, cooperative cancellation, worker ownership and a local run-once worker that executes queued EDA verification and persists evidence; lease recovery, multi-host queue, authenticated identity, API integration and mid-run cancellation remain |
| 44 | Resource budget estimation | Partial | Calibrate estimates from measured history while retaining hard limits |
| 45 | Artifact retention and cleanup | Partial | Integrate cleanup with worker lifecycle and retention enforcement |
| 46 | Configuration validation | Partial | Integrate preflight validation into every run path and revalidate at execution time |
| 47 | Tool adapter contract tests | Implemented baseline | Expand per-tool/version matrix and real-tool regression coverage |
| 48 | User-facing failure explanations | Implemented baseline | Expand grounded guidance while retaining raw logs and uncertainty labels |
| 49 | Accessibility and keyboard-first UI | Not implemented | This repository is currently a Python CLI/engine; a UI must exist before UI accessibility can be implemented |
| 50 | Benchmark and acceptance dashboard | Partial | Generate a dashboard from verified CI/test evidence and supported-tool manifests |

## New CLI capabilities

The branch includes commands for input inventory, run identity, policy evaluation, SBOM generation, flaky-run analysis, failure clustering, coverage import, evidence scorecards, provenance, approval records, waiver validation, change-impact mapping, resource estimates, workspace cleanup, retention records, mutation-score accounting, golden-corpus validation, regression history, failure-subset suggestions, and config preflight.

## Important limitations

- Local approval/waiver helpers do not provide authenticated identity, durable authorization or a protected server-side register.
- The mutation score command computes metrics from observed outcomes; it does not yet mutate and simulate RTL itself.
- The failure minimizer suggests a subset from supplied failure mappings; it does not rerun tests to prove reproduction.
- The OpenAPI file is a reference contract, not a running API service.
- No result from this tracker constitutes fabrication readiness, safety certification, or defence certification.

## Job lifecycle implementation added

The `mqv_eda.job_queue` module now provides a SQLite-backed, single-host queue with:
- durable job records and ordered state-transition events;
- atomic queued-job claims using SQLite write transactions;
- explicit state-transition validation and terminal-state protection;
- queued cancellation and cooperative cancellation requests for running work;
- list, inspect and queue-health operations.

CLI entry point: `python -m mqv_eda jobs --db .mqv/jobs.sqlite3 <list|health|submit|show|claim|cancel|finish>`.

This is **not yet a distributed queue or a complete background execution service**. A worker must poll a running job's `cancel_requested` field and acknowledge cancellation. The CLI's `finish` command records a worker-reported outcome; it does not itself execute or terminate an EDA process. SQLite is appropriate for a local/single-host prototype, not multi-host production scheduling.


## Latest incremental implementation — durable waiver register

The `mqv_eda.waiver_register` module now persists scoped policy exceptions in SQLite, requires a non-empty rationale and future expiry, records creation/revocation events, supports revocation, and evaluates scope using exact-match context keys. The `mqv-eda waivers` CLI exposes create/list/show/revoke operations.

This is a local governance primitive, not a trusted authorization service: actor names are caller-supplied, wildcard matching is intentionally not implemented, and the register is not yet wired as an automatic policy bypass or release approval. Treat waivers as records for review; do not assume a record alone authorizes a release.


## Latest incremental implementation — guarded retention actions

The retention CLI now supports a dry-run by default and an explicit `--execute` switch. File archive operations require a new destination and verify the copied SHA-256 digest. File deletion requires `--confirm-sha256` matching the current source digest. Symlinks and directories are rejected. Automated tests cover dry-run behavior, verified archive copies, digest-gated deletion, destination collision, and symlink/directory rejection.

This is not yet a complete retention service: there is no scheduler, immutable external audit store, multi-user authorization, directory-level retention policy, or legal hold workflow. Use deletion only on dedicated, backed-up evidence paths.


## Latest incremental implementation — accessible evidence report

The generated HTML report now provides a semantic run-summary section, check counts, table caption and scoped headers, responsive layout, visible keyboard focus, print styling, and escaped user/tool text. A regression test checks those properties. This improves the accessible report artifact; it does not constitute a full interactive dashboard or a formal WCAG conformance audit.


## Latest incremental implementation — broader SBOM inventory

The SBOM output now includes a separate native EDA-tool inventory for configured tool adapters, reporting executable lookup state, resolved path, declared purpose, tier, and integration level. It explicitly leaves version and trust status unverified instead of implying that a PATH hit is a trusted toolchain attestation. Python package inventory remains available. Full native binary hashes, OS package inventory, proprietary tool metadata, PDK inventory, and official CycloneDX schema validation are still outstanding.


## Latest incremental implementation — job ownership check

The local queue now rejects terminal job completion reports unless the supplied worker ID matches the worker recorded when the job was claimed. This prevents accidental or naive cross-worker completion in the local queue API and is covered by a regression test. Worker IDs remain caller-supplied labels, not cryptographically authenticated identities; a trusted worker service and lease/recovery protocol are still required for hostile or multi-tenant environments.


## Latest incremental implementation — local EDA job worker

The `jobs run-once --worker-id ID` command now atomically claims one queued job, executes the verification engine against the job payload's `source`, writes JSON/HTML evidence with job ID, worker label, input/run identity and toolchain snapshot, and records SUCCEEDED only when the aggregate result is PASS. Non-PASS verification results are recorded as FAILED; unexpected execution errors are recorded as worker failures. An empty queue returns IDLE.

Example payload:

```json
{
  "source": "./rtl-project",
  "output_dir": "./artifacts/job-001",
  "top": "top_module",
  "testbenches": ["tb/top_tb.sv"],
  "timeout": 120
}
```

This is a single-host worker prototype, not a continuously supervised worker pool. Cancellation is not yet polled during an active EDA process, worker leases/recovery are absent, and worker IDs are labels rather than authenticated identities. Run only with trusted local job payloads.


## Latest incremental implementation — baseline freshness gate

Use `python -m mqv_eda baseline-freshness baseline-report.json current-report.json --max-age-seconds 604800` to evaluate a baseline. The command blocks missing or invalid timestamps, future-dated baselines, baselines older than the configured limit, and (by default) missing or changed source revisions. It emits a JSON decision and exits non-zero for stale or unverifiable baselines. `--allow-revision-change` is an explicit override and should only be used when the release policy permits cross-revision baselines.

The gate evaluates freshness metadata; it does not prove semantic equivalence, execute a rerun, or approve a release.


## Latest incremental implementation — report-bound run identity

The normal `verify` path and local queue worker now attach a run-identity envelope and toolchain discovery snapshot to the JSON report metadata. The identity binds the project input fingerprint, selected run configuration, source revision when available, and discovered toolchain snapshot. The toolchain record includes detected versions where the probe supports them and missing-tool state; it does not yet hash or cryptographically attest native executables.


## Latest incremental implementation — automatic provenance output

Every standard `verify` run and local queued worker now writes `provenance.json` beside the report. The record binds the run ID/fingerprint and source revision where available to the report's SHA-256, size and filename label. The provenance JSON itself is not signed, and the current report link does not include an evidence bundle; use detached evidence signing and independently pinned trust keys when authenticity is required.


## Latest incremental implementation — license/notice inventory

Run `python -m mqv_eda license-inventory ./vendor --out license-inventory.json` to hash license/notice-like files and extract explicit SPDX identifiers where present. Files without an SPDX tag are marked for manual review; symlinks are rejected. This is a discovery aid only: it does not infer license permission, determine compatibility, or replace upstream notice preservation and legal review.
