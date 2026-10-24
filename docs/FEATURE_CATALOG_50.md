# MAH Quantum Verify / Aegis — 50 High-Value Engineering Features

**Purpose:** Prioritized product backlog of less-obvious capabilities that make a verification platform trustworthy, repeatable, reviewable, and practical for serious engineering teams.

**Status discipline:** This is a proposed implementation backlog, not a claim that these 50 features already exist. Existing capabilities must be verified against code and automated tests before they are marked shipped. “Release gate” below means a software policy result eligible for human review, not hardware safety certification or fabrication approval.

## Priority key

- **P0 — Trust foundation:** implement before positioning the product for sensitive or high-assurance engineering workflows.
- **P1 — Daily engineering value:** strong differentiation for verification teams.
- **P2 — Scale and enterprise operations:** important as teams and projects grow.

## A. Evidence integrity and reproducibility

1. **Immutable run identity (P0).** Assign every run a unique ID and bind it to the source revision, input hashes, configuration, toolchain, and start/end times. *Acceptance:* any changed input changes the run fingerprint.
2. **Complete input inventory (P0).** Enumerate RTL, testbenches, constraints, scripts, libraries, environment variables allowed by policy, and included files. *Acceptance:* missing or untracked inputs are surfaced before execution.
3. **Toolchain identity snapshot (P0).** Record executable path, version output, binary digest where practical, and adapter version. *Acceptance:* missing or changed tool identity is explicit in the report.
4. **Reproducible-run comparison (P0).** Rerun identical inputs and compare normalized outcomes and selected artifacts. *Acceptance:* distinguish exact match, expected nondeterminism, and unexplained divergence.
5. **Evidence bundle manifest verification (P0).** Validate file membership, sizes, and SHA-256 hashes before a bundle is trusted. *Acceptance:* tampering, missing files, duplicate paths, and traversal paths fail closed.
6. **Detached evidence signatures (P0).** Support signing and verifying evidence bundles with an independently trusted public key. *Acceptance:* tampered bundles fail verification; key trust is documented separately.
7. **Evidence retention policy (P1).** Define per-project retention, archival, and deletion behavior. *Acceptance:* report what was retained or removed and when.
8. **Portable evidence export (P1).** Export a documented, tool-neutral JSON summary plus original logs and reports. *Acceptance:* bundle can be inspected without the platform UI.
9. **Evidence completeness scorecard (P1).** Show which expected evidence exists, is missing, stale, or invalid. *Acceptance:* score is explainable by individual evidence items, not a black-box percentage.
10. **Run provenance chain (P1).** Link source revision, run, report, comparison, triage, and signed evidence bundle. *Acceptance:* each link resolves to a stable ID or explicit “not available.”

## B. Policy and release governance

11. **Configurable verification policy engine (P0).** Evaluate reports against project-defined mandatory checks and evidence requirements. *Acceptance:* absent, failed, blocked, or inconclusive mandatory checks prevent eligibility.
12. **Fail-closed missing-evidence behavior (P0).** Treat missing required stages, unknown statuses, malformed reports, and unavailable artifacts as blockers. *Acceptance:* negative tests prove no missing evidence can silently pass.
13. **Policy versioning (P0).** Include policy ID and version in every decision. *Acceptance:* the same report evaluated against two policy versions produces separately traceable results.
14. **Human approval gate (P0).** Require an authorized reviewer for designated high-impact transitions. *Acceptance:* decision records reviewer identity, timestamp, scope, and rationale.
15. **Separation of duties (P1).** Allow policy authors, run operators, and final reviewers to be distinct roles. *Acceptance:* prohibited self-approval is tested.
16. **Waiver and exception register (P1).** Record approved deviations with owner, reason, expiry, and scope. *Acceptance:* expired or out-of-scope waivers do not satisfy a gate.
17. **Policy dry-run mode (P1).** Preview which rules would block a report without changing its status. *Acceptance:* output clearly states it is advisory and cannot approve a release.
18. **Baseline freshness rules (P1).** Require evidence to be newer than a configured age or source change. *Acceptance:* stale evidence is reported and blocks only when policy says so.
19. **Change-impact rule mapping (P1).** Map changed files or constraints to checks that should be rerun. *Acceptance:* every skipped check has an explicit reason and policy basis.
20. **Decision explanation report (P1).** Produce a machine-readable and human-readable list of passed rules, blockers, warnings, and required actions. *Acceptance:* every decision is traceable to concrete evidence.

## C. Regression quality and defect discovery

21. **Regression history and trend view (P1).** Track pass/fail/inconclusive counts and run durations over time. *Acceptance:* trends link back to underlying runs and never hide failed checks.
22. **Changed-check detection (P1).** Highlight new failures, recovered failures, removed checks, and changed inputs. *Acceptance:* removal of a previously required check is surfaced.
23. **Failure clustering (P1).** Group similar failures by normalized signature while preserving raw logs. *Acceptance:* clusters can be expanded to individual evidence.
24. **Deterministic log triage (P1).** Identify common syntax, elaboration, assertion, timeout, and timing patterns using transparent rules. *Acceptance:* suggestions are labelled heuristics, not root-cause proof.
25. **Flaky-test detector (P1).** Identify outcomes that vary across repeated runs with identical inputs. *Acceptance:* reports sample count and observed variation, without automatically dismissing failures.
26. **Mutation-test benchmark (P1).** Run curated intentionally faulty RTL variants to measure whether checks catch seeded defects. *Acceptance:* publish detected and missed mutants with reproducible fixtures.
27. **False-pass / false-failure metrics (P1).** Maintain benchmark-derived quality measures for supported test corpora. *Acceptance:* methodology, denominator, and test set are included.
28. **Coverage trend ingestion (P2).** Import supported line, branch, toggle, or functional coverage reports. *Acceptance:* distinguish unavailable coverage from zero coverage and record tool format/version.
29. **Regression minimization (P2).** Identify a smaller failing test subset where the test format supports safe minimization. *Acceptance:* original test remains preserved and minimized case reproduces the failure.
30. **Golden-corpus versioning (P1).** Version known-good and known-bad fixtures with expected outcomes. *Acceptance:* changing expected results requires review and a rationale.

## D. Security and customer-controlled execution

31. **Worker isolation contract (P0).** Document and test CPU, memory, wall-time, process, filesystem, and network boundaries. *Acceptance:* adversarial tests verify configured limits on the target host.
32. **No-network execution mode (P0).** Run approved jobs without outbound network access. *Acceptance:* test job completes from staged inputs and fails clearly if a missing dependency requires network access.
33. **Workspace path containment (P0).** Prevent symlink, traversal, and output-path escapes. *Acceptance:* malicious paths are rejected before file writes or process launch.
34. **Secret-safe logging (P0).** Redact configured secrets and avoid logging credentials or private key material. *Acceptance:* tests inject sentinel secrets and confirm they do not appear in logs or reports.
35. **Dependency inventory / SBOM (P0).** Generate a versioned inventory of product and toolchain dependencies. *Acceptance:* inventory records source/version/license metadata where known and marks unknowns explicitly.
36. **License and notice inventory (P0).** Preserve upstream notices and identify unresolved redistribution reviews. *Acceptance:* release packaging fails when required notices are missing from the configured inventory.
37. **Signed build provenance (P1).** Record build inputs, builder identity, and output hashes; optionally sign the provenance statement. *Acceptance:* provenance can be independently checked and trust roots are documented.
38. **Customer-managed worker mode (P0).** Keep sensitive RTL and execution artifacts on a customer-controlled host while the UI/control plane handles only approved metadata. *Acceptance:* a test proves source files are not uploaded to the control plane.
39. **Role and action audit (P1).** Log sensitive actions with actor, action, target, timestamp, and outcome. *Acceptance:* audit entries are append-only at the application layer and tampering is detectable.
40. **Incident-ready execution record (P2).** Preserve job termination reason, resource-limit events, worker identity, and relevant security events. *Acceptance:* an operator can reconstruct why a job stopped without exposing secrets.

## E. Engineering usability and integration

41. **Stable machine-readable CLI contract (P1).** Version command output schemas and exit codes. *Acceptance:* tests lock down success, policy-blocked, invalid-input, and internal-error exit codes.
42. **API schema and compatibility policy (P2).** Publish a versioned API contract for projects, jobs, reports, and evidence. *Acceptance:* breaking changes require a version increment and compatibility tests.
43. **Queue and cancellation semantics (P1).** Define queued, running, cancelling, cancelled, timed-out, and completed states. *Acceptance:* cancellation cannot be misreported as a passing verification.
44. **Resource budget estimation (P2).** Estimate job resource needs from project/tool profile and historical data where available. *Acceptance:* estimates show uncertainty and do not replace hard worker limits.
45. **Artifact retention and cleanup (P1).** Remove temporary workspaces safely after completion or retention expiry. *Acceptance:* cleanup never deletes another job’s files and reports cleanup failures.
46. **Configuration validation before execution (P0).** Validate tool paths, project settings, constraints, and policy references before launching jobs. *Acceptance:* invalid configuration fails early with actionable diagnostics.
47. **Tool adapter contract tests (P1).** Test each adapter’s command, timeout, exit-code interpretation, output parsing, and version detection. *Acceptance:* unsupported tool versions are surfaced rather than silently misparsed.
48. **User-facing failure explanations (P1).** Translate common failure patterns into evidence-linked explanations and next steps. *Acceptance:* raw logs remain accessible and heuristic confidence is not overstated.
49. **Accessibility and keyboard-first UI (P2).** Support keyboard navigation, visible focus, semantic labels, and readable status distinctions. *Acceptance:* core workflows pass automated accessibility checks plus manual review.
50. **Benchmark and acceptance dashboard (P1).** Track supported tools, tested versions, fixture coverage, known limitations, and latest verified CI evidence. *Acceptance:* dashboard never presents a planned or untested capability as shipped.

## Suggested implementation sequence

**Wave 1 — Trust before breadth:** 1–6, 11–16, 31–38, 46.  
**Wave 2 — Daily engineering value:** 8–10, 20–27, 30, 39, 41, 43, 45, 47, 48, 50.  
**Wave 3 — Scale and polish:** 7, 17–19, 28–29, 40, 42, 44, 49.

## Release discipline

A feature is **implemented** only when code exists. It is **verified** only when automated tests exercise success and failure cases. It is **production-ready** only after deployment-specific threat testing, operational validation, documentation, and appropriate independent review. Defence, safety, or fabrication-signoff claims require the applicable external evidence and authorization; this backlog alone provides none.
