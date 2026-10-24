# MAH Quantum Aegis — Differentiation and Defence Readiness Plan

Status: engineering requirements and roadmap, not a claim of completed capabilities, certification, or procurement eligibility.

## 1. Product thesis

MAH Quantum Aegis should be positioned as a **tool-integrated RTL verification, regression, and engineering-evidence platform**. Its job is to make supported hardware verification workflows reproducible, reviewable, and easier to operate across approved tools.

It must not be positioned as a replacement for every commercial EDA suite, a certified safety system, or an automatic fabrication-readiness authority.

### The customer problem we aim to solve

Engineering teams often need to coordinate several independent tools, scripts, testbenches, configurations, logs, and reports. Aegis should reduce the manual work needed to orchestrate supported jobs, compare revisions, investigate failures, and assemble traceable evidence.

The value proposition must be proven by benchmarks and customer workflows, not asserted in marketing.

## 2. Differentiators to implement and prove

### A. Reproducible verification runs
- Store the exact RTL revision/hash, constraints, configuration, tool versions, environment identity, and run parameters.
- Capture stdout/stderr, exit codes, timeouts, resource limits, and all generated reports.
- Make reruns reproducible and clearly record when a result cannot be reproduced.
- Separate simulation pass, lint result, formal proof result, timing result, and physical-design result. Never collapse these into a single unqualified "chip passed" result.

### B. Cross-tool evidence workspace
- Provide one job/project model for supported simulators, lint tools, formal tools, synthesis and timing tools.
- Preserve each tool's original output while adding a normalized result schema.
- Show the exact source and configuration associated with each finding.
- Export portable evidence bundles in documented formats.

### C. Regression and fault-detection intelligence
- Compare runs across revisions and identify newly failing tests and changed metrics.
- Maintain a curated reference corpus with known-good designs and deliberately faulty variants.
- Measure fault-detection rate, false-pass rate, false-failure rate, runtime, and repeatability.
- Keep benchmark inputs, test methodology, tool versions, and results available for independent reproduction.

### D. Customer-controlled deployment
- Design for a local or customer-managed deployment option, subject to actual implementation and support constraints.
- Default to no source-code upload to external services and no telemetry of design content.
- Make network access explicit, configurable, and testable; support a documented no-network operating mode only after it has been tested.
- Do not advertise "air-gapped" or "offline" until clean-environment tests demonstrate no hidden network dependencies.
- Provide data-flow diagrams and a clear inventory of files written, retained, exported, and deleted.

### E. Open integrations, not hidden dependencies
- Integrate with customer-approved tools where technically and legally supported.
- Provide a stable CLI, documented APIs, versioned configuration, and CI adapters.
- Preserve upstream license notices and generate an accurate software bill of materials (SBOM).
- Clearly identify third-party components and distinguish them from original MAH Quantum code. Do not remove notices or imply that third-party tools are owned by MAH Quantum.

## 3. Defence-oriented readiness requirements

Defence buyers do not select software because it says "defence-grade." They need evidence that the product meets the particular procurement, security, operational, legal, and technical requirements for the intended deployment.

### Security and data custody
- Threat model covering malicious RTL, testbenches, archives, scripts, dependencies, plugins, and generated artifacts.
- Isolated job execution with least privilege, bounded CPU/memory/disk/time, controlled filesystem access, and no host-secret exposure.
- Strong authentication, role-based access control, separation of duties, and auditable administrative actions for multi-user deployments.
- Encryption in transit and at rest where applicable, managed keys, backup/restore tests, and documented retention/deletion policies.
- Signed release artifacts and verifiable hashes; protected build/release credentials; dependency vulnerability handling.
- Security incident response, vulnerability disclosure, patch policy, and release advisories.
- Independent security assessment by an appropriately qualified provider before handling sensitive customer workloads.

### Supply-chain transparency
- Generate a machine-readable SBOM for each release, including component names, versions, hashes, licenses, and provenance where available.
- Pin dependencies to immutable revisions or verified release artifacts.
- Record build inputs and release provenance; verify artifact signatures where upstream provides them.
- Maintain a license and redistribution review for all source, binary, PDK, library, and rule-deck components.
- Do not bundle customer-restricted, export-controlled, foundry-confidential, or otherwise non-redistributable materials without explicit authorization.

### Offline and restricted-network operation
- Build and install from a reviewed, pre-staged package with documented dependencies.
- Demonstrate installation and representative verification runs in a clean network-disabled environment.
- Test that the product does not attempt unexpected DNS, HTTP, telemetry, update, or package-manager requests.
- Provide a signed update process, removable-media import/export controls, and verification of transferred artifacts where the customer requires them.
- State precisely what is offline-capable; do not imply that every optional tool or physical-design flow works offline before it is validated.

### Audit and operational controls
- Append-only or tamper-evident audit events for user, project, configuration, tool, and release actions.
- Documented user roles, access reviews, backup procedures, recovery objectives, and administrator controls.
- Secure default configuration and hardening guide.
- A release-specific security package: architecture, data-flow diagram, threat model, SBOM, vulnerability process, test evidence, and known limitations.
- Support customer-required independent audit, source review, and third-party security assessment subject to contract and applicable law.

### Verification integrity
- Preserve native logs and raw tool results alongside normalized summaries.
- Report tool crashes, unsupported constructs, missing constraints, incomplete runs, and inconclusive formal results as explicit states—not as passes.
- Keep human approval and engineering sign-off separate from automated checks.
- Do not claim safety, mission assurance, security assurance, or fabrication readiness from a partial set of tests.

## 4. Why a defence customer might evaluate Aegis

Aegis can earn consideration if it demonstrates several practical advantages in a specific use case:
1. **Data control:** designs can remain in a customer-controlled environment when the deployment has been implemented and approved for that use.
2. **Traceability:** reviewers can identify which design, toolchain, configuration, and evidence produced each result.
3. **Integration flexibility:** the customer can retain approved tools and integrate Aegis without replacing its entire engineering stack.
4. **Repeatability:** the same controlled inputs produce comparable results, and differences are explained.
5. **Supply-chain visibility:** dependencies, hashes, licenses, and release provenance are documented.
6. **Supportability:** installation, failure recovery, updates, documentation, and maintenance are part of the delivered product.

These are hypotheses to validate through interviews, pilot projects, independent review, and measurable benchmarks. They are not evidence that a defence organization will choose or approve Aegis.

## 5. Adoption strategy

Start with an unclassified, non-sensitive pilot with a university laboratory, semiconductor startup, or engineering team. Use synthetic/reference RTL or customer-approved non-sensitive designs.

Pilot success criteria:
- A defined baseline workflow and a measured Aegis workflow.
- Correct expected results on a documented reference corpus.
- Measured fault-detection, false-pass/false-failure, runtime, and reproducibility metrics.
- Reproduction by an engineer who did not author the tests.
- A complete evidence package and a documented list of limitations.
- Security and deployment review completed for the pilot's actual data classification.
- Written customer feedback and a concrete next-step decision.

Only after a successful pilot should Aegis be proposed for more sensitive use cases. A defence buyer may require vendor due diligence, security audits, certifications, approved hosting, procurement registration, contractual conditions, or other controls. Requirements differ by customer, country, project, and data classification; confirm them with the relevant procurement and security authorities before making commitments.

## 6. Release gates

### Gate 1 — Engineering credibility
- Golden regression corpus and fault-injection suite.
- Reproducible test reports and known limitations.
- CI success on clean runners and documented local setup.

### Gate 2 — Toolchain custody
- Selected source packs imported and verified.
- License review and SBOM generated.
- Offline behavior tested for the explicitly supported configuration.

### Gate 3 — Product security
- Threat model, isolated execution, access control, audit logging, secure release process.
- Independent security review and tracked remediation of findings.

### Gate 4 — Customer evidence
- Independently reproducible benchmark results.
- Successful pilot with written acceptance criteria and results.
- Support, maintenance, incident response, and release documentation.

### Gate 5 — Restricted/defence deployment consideration
- Customer-specific security and procurement requirements mapped.
- Required audits/certifications completed if applicable.
- Written authorization for the intended environment and data.
- No unsupported claims about accreditation, certification, or suitability for classified workloads.

## 7. What we must not claim without evidence

Do not claim:
- "Defence-grade", "military-certified", "air-gapped", or "classified-ready" without the specific evidence and authorization that substantiate the claim.
- That Aegis replaces commercial EDA suites or can sign off any processor for fabrication.
- That all third-party tools are proprietary MAH Quantum technology.
- That source availability automatically permits redistribution.
- That a passing CI run proves all integrations, security properties, or production flows are complete.

## 8. Reference frameworks and reading

These are useful engineering references, not a declaration of compliance:
- NIST Secure Software Development Framework (SP 800-218): https://csrc.nist.gov/pubs/sp/800/218/final
- NIST software supply-chain security and SBOM guidance: https://www.nist.gov/itl/executive-order-14028-improving-nations-cybersecurity/software-supply-chain-security-guidance-20
- Joint SBOM guidance from national cybersecurity agencies (2025): https://media.defense.gov/2025/Sep/03/2003791481/-1/-1/0/JOINT-GUIDANCE-A-SHARED-VISION-OF-SOFTWARE-BILL-OF-MATERIALS-FOR-CYBERSECURITY.PDF
- India Ministry of Defence procurement-related materials: verify the current applicable Defence Procurement Manual, tender conditions, security requirements, and buyer-specific requirements with the relevant authority before relying on any clause.

## Definition of success

Aegis earns trust when a technically independent customer can install it, understand its data handling, reproduce its results, inspect its dependencies, review its security posture, and measure a real improvement over their existing workflow. Trust is earned through evidence, not slogans.
