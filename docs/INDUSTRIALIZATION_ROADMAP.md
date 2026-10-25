# MQV Industrialization Roadmap

## Current position

MQV is an early-stage EDA orchestration prototype. Current integrations cover selected RTL checks, simulation, synthesis, user-supplied formal tasks, static timing when required inputs are supplied, and selected KLayout DRC workflows. The verification catalogue is a coverage plan, not a list of fully implemented engines. A successful sample run is not industrial sign-off.

## Product gates

### Gate A — Trustworthy verification kernel
- Fail-closed status semantics for every tool adapter.
- Required-input validation before launch; missing prerequisites become BLOCKED.
- Deterministic input inventory and cryptographic digests; tool versions and command/configuration captured.
- Bounded execution, logs, timeouts, cancellation and worker isolation tested adversarially.
- Regression tests for clean, failing, missing-input, malformed-report, timeout and tool-crash cases.
- Machine-readable report schema with stable versioning and evidence provenance.

### Gate B — Real multi-stage design verification
- Project manifest describing top, source sets, include paths, defines, clocks, resets, constraints, libraries, PDK and process corners.
- Dependency graph that schedules only applicable stages and explicitly blocks stages with missing prerequisites.
- Validated RTL simulation and coverage flow, assertions, formal properties, equivalence, CDC/RDC and DFT integration where tool capability and design inputs allow.
- Multi-mode/multi-corner STA, unconstrained path checks, timing exceptions review, power analysis, and physical design stages with qualified inputs.
- PDK-specific DRC/LVS/ERC integrations validated against official golden and intentionally failing fixtures; no generic deck substitution.
- Stage-level and whole-project reports that distinguish tool execution success from engineering acceptance.

### Gate C — Scale and repeatability
- Hierarchical/IP/subsystem/SoC project model, incremental builds, dependency-aware caching and safe invalidation.
- Parallel scheduling with resource quotas, cancellation, retry policy and reproducible job manifests.
- Large regression support, coverage trend tracking, triage, waiver ownership/expiry and requirement-to-test traceability.
- Benchmarks published for runtime, memory, scale and reproducibility on named hardware and designs.

### Gate D — Industrial deployment
- Threat model and independent security review; validated isolation, tenant separation, secrets handling, audit controls, backups and incident response.
- SBOM, pinned dependencies, signed releases/artifacts, vulnerability management and supply-chain controls.
- Licensed EDA tools/PDKs handled under explicit entitlements and local/on-prem deployment options for confidential IP.
- Versioned API/CLI, documented installation/upgrade/rollback, observability, support process and compatibility policy.
- External design-partner acceptance on authorized designs with measurable defect detection, false-positive rate, runtime and report quality.

### Gate E — Commercial proof
- Clear customer segment and use case; interviews and design-partner commitments.
- Demonstrated advantage over a defined baseline, backed by benchmark data and reproducible case studies.
- Pricing based on customer value, tool/licence costs, deployment/support costs and procurement feedback.
- Reference customers, paid pilots or contracts, renewal/expansion evidence and support economics.

## Readiness policy

`mqv_eda/readiness.py` provides an initial evidence inventory policy. It requires an explicit scope, known required verification-unit IDs, unique evidence records, PASS status, an evidence URI, and an input digest; human review is required by default. It returns `INCOMPLETE`, `BLOCKED`, `NOT READY`, `REVIEW REQUIRED`, or `EVIDENCE COMPLETE — SIGN-OFF STILL REQUIRED`. It intentionally never returns a fabrication-ready verdict. This policy currently does not authenticate artifact contents, validate digest formats against files, or replace independent engineering review.

## $500K milestone interpretation

A $500,000 target should be supported by evidence of value, not a feature count. Relevant paths differ: an asset/acquisition valuation, a priced equity financing, and annual revenue are not equivalent. Before asserting a valuation, establish a working product, reproducible benchmarks, customer demand, defensible technical differentiation, licensing/compliance readiness, and credible revenue or investment terms. No valuation is guaranteed by completing this roadmap.

## Execution rule

Changes stay on feature branches until automated tests pass and the diff is reviewed. Never mark a planned integration as implemented solely because it appears in the catalogue. Do not run proprietary or restricted designs in public hosted CI without authorization and suitable controls.
