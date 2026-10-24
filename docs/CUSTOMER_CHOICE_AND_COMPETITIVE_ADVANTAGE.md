# MAH Quantum Aegis — Customer Choice and Competitive Advantage Backlog

This document turns the product positioning into implementation work. It is a backlog of goals and acceptance tests, not a claim that these features are already complete.

## North-star promise

**Aegis should make supported hardware verification workflows easier to reproduce, investigate, compare, and audit—without forcing customers to replace their approved EDA tools or surrender control of their design data.**

We must prove this promise on reference designs and customer-approved pilot workflows.

## 1. Why an engineering team would choose Aegis

### Differentiator 1: One evidence chain across multiple tools
Build a project/run model that connects the design revision, constraints, testbench, tool versions, commands, logs, findings, reports, and result state. Keep native tool output available alongside normalized summaries.

Acceptance tests:
- Every result points to immutable input/configuration hashes and tool identity.
- A missing prerequisite produces BLOCKED, not PASS.
- A timeout or crash produces ERROR or an explicit incomplete state.
- A reviewer can export the run and inspect its raw evidence without Aegis-specific access.

### Differentiator 2: Failure triage that saves engineering time
Build a failure view that groups related errors, extracts source locations and signal/test context when the tool provides them, links to relevant log sections, and compares the failure with a previous passing run.

Acceptance tests:
- Seeded failures are mapped to the correct test and source/log location.
- The UI distinguishes parsed facts from inferred suggestions.
- AI-generated explanations cite the exact log/source fragments they rely on.
- The system never changes RTL automatically without explicit approval.
- Measure time-to-diagnosis against a documented manual baseline.

### Differentiator 3: Fault-detection scorecard
Create a public reference suite of good and faulty designs: arithmetic units, counters, FIFOs, arbiters, FSMs, pipelines, reset behavior, parameter edge cases, and selected protocol checks.

Acceptance tests:
- Each fixture has a documented expected outcome and defect description.
- Mutation operators introduce controlled defects.
- Report detected/missed mutations, false passes, false failures, runtime, and tool versions.
- Do not publish a single “coverage” percentage unless its definition and denominator are stated.
- Independent engineers can reproduce the benchmark from a clean checkout.

### Differentiator 4: Regression intelligence
Compare runs and revisions, classify new versus existing failures, highlight changed metrics, and support rerunning failed tests.

Acceptance tests:
- Identical inputs produce equivalent normalized results in repeated runs, except for explicitly documented nondeterminism.
- A deliberately introduced regression is identified.
- The comparison identifies missing evidence or changed tool versions rather than silently comparing incompatible runs.

### Differentiator 5: Portable engineering evidence
Create a versioned evidence bundle containing a machine-readable summary, HTML report, original logs, relevant reports, input hashes, tool inventory, configuration, timestamps, result states, and limitations.

Acceptance tests:
- Bundle schema is versioned and documented.
- Export/import validation detects missing or changed files.
- Evidence bundle is self-contained for the claims it makes; it does not pretend to contain unavailable tools or restricted collateral.
- Hashes detect accidental modification; cryptographic signatures and identity-backed signing are a separate later control.

### Differentiator 6: Bring-your-own-toolchain
Support approved customer installations and stable adapters for tool discovery, version checks, command execution, result parsing, and capability reporting.

Acceptance tests:
- Each integration has a tested version range and supported/unsupported matrix.
- Missing executables and incompatible versions are clearly explained.
- The same interface can invoke more than one supported backend where appropriate.
- Tool licensing remains the customer's responsibility where applicable.

### Differentiator 7: Customer-controlled operation
Provide a deployable local/customer-managed mode with explicit network behavior, restricted execution, storage controls and clear retention settings.

Acceptance tests:
- A clean network-disabled test proves the declared offline subset works.
- Network egress tests detect unexpected DNS/HTTP attempts.
- Jobs run with least privilege and explicit resource limits.
- Malicious archives and RTL/testbench inputs are tested against isolation boundaries.
- Data-flow and threat-model documentation matches observed behavior.

### Differentiator 8: Constraint and evidence gap analysis
Identify missing prerequisites and suspicious configurations before interpreting results. Examples include missing timing constraints, absent Liberty files, incompatible platform collateral, unrun checks, unsupported constructs, and incomplete formal assumptions.

Acceptance tests:
- Each diagnostic has a rule ID, severity, evidence and remediation guidance.
- Findings distinguish confirmed problems from heuristics.
- Aegis reports the scope of analysis and does not claim sign-off from incomplete checks.

## 2. Why a defence customer might consider Aegis

Defence adoption is not a marketing feature; it is a customer-specific qualification and procurement process. Aegis should be designed to make a serious evaluation possible, while making no unsupported accreditation or classified-readiness claims.

### Defence requirement A: Source and data custody
- Local/customer-managed deployment option.
- Explicit network and telemetry behavior.
- Clear data retention, export, deletion and backup policies.
- No use of customer designs for model training or external services unless explicitly authorized by contract and customer policy.
- Demonstrated restricted-network behavior before describing a deployment as offline.

### Defence requirement B: Security architecture
- Threat model for untrusted RTL, testbenches, archives, plugins, parsers and tool execution.
- Worker isolation, least privilege, filesystem allowlists, resource limits and no host-secret access.
- Role-based access controls, administrative audit events, secure secrets handling and tested recovery.
- Independent security review, tracked remediation and a vulnerability disclosure/patch policy.
- Customer-specific review before any restricted or classified use.

### Defence requirement C: Software supply-chain accountability
- SBOM for each product release.
- Pinned dependencies, artifact hashes and provenance.
- License/redistribution review for tools, PDKs, libraries and rule decks.
- Reproducible build records where technically feasible.
- Signed releases and controlled update procedures.
- Clear separation between MAH Quantum-authored code and third-party components.

### Defence requirement D: Reviewable engineering evidence
- Raw logs and reports retained with normalized result summaries.
- Inconclusive, blocked, failed and incomplete runs remain distinct.
- Traceability from run to design/configuration/tool versions.
- Human approval remains separate from automated results.
- Customer can independently reproduce agreed acceptance tests.

### Defence requirement E: Operational maturity
- Documented installation, hardening, upgrades, backup/restore and recovery.
- Supported-tool matrix and known-limitations register.
- Release notes, maintenance policy and support escalation process.
- Customer-specific procurement, security and certification requirements mapped before commitments.

## 3. Build the moat around original MAH Quantum work

Open-source tools alone are not a durable competitive moat. Keep all upstream license notices intact and build proprietary differentiation in independently authored modules where appropriate:

1. Aegis run orchestration and normalized evidence model.
2. Cross-tool traceability and regression comparison.
3. Failure grouping and source/log navigation.
4. Curated fault-injection and benchmark corpus.
5. Policy-driven workflow gates and evidence completeness analysis.
6. Customer deployment controls and administration.
7. Integrations, documented APIs, release engineering and support.

A proprietary module does not automatically make the whole distribution proprietary; each component and modification must respect its applicable license.

## 4. Measure customer value, not feature count

For each pilot, record a baseline and compare Aegis against it:
- Median time to diagnose a seeded failure.
- Defect/mutation detection rate and false-pass rate.
- Time required to prepare an engineering evidence package.
- Percentage of runs reproducible by another engineer.
- Number of manual handoffs and tool invocations.
- Setup time on a clean machine.
- Runtime and resource consumption.
- Number of unresolved prerequisites or evidence gaps surfaced before sign-off review.

Publish methods, denominators, versions and limitations with the results. Do not cherry-pick one favorable run.

## 5. Product acceptance gates

### Gate 1 — Trustworthy core
Golden corpus, negative tests, mutation scorecard, explicit result states, reproducible reports.

### Gate 2 — Useful daily workflow
Regression comparison, failure triage, evidence export, stable CLI/API, supported tool adapters.

### Gate 3 — Controlled deployment
Threat model, worker isolation, data-flow documentation, SBOM, dependency/license review, clean offline subset test.

### Gate 4 — Independent validation
External reproduction of benchmark results, independent security review, customer-approved pilot, tracked remediation.

### Gate 5 — Defence evaluation readiness
Requirements matrix for the actual buyer and deployment, required procurement/security checks, support and maintenance commitments, and written evidence for every claim.

## 6. Release rule

A feature is not considered complete because code exists or a CI workflow passes. It is complete only when its behavior, failure modes, acceptance tests, limitations and evidence are documented and reviewed.

The product must never infer fabrication readiness, mission assurance, or defence approval from a partial set of successful automated checks.
