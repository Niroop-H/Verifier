# Session 2 — Threat Model and Worker Security Contract

## Status and scope

This document describes the current engineering threat model for MAH Quantum Verify (MQV) and the minimum deployment contract for processing untrusted or customer-provided design inputs. It is a design control, not evidence that a deployed service already enforces every control below.

The current repository is public and the local engine is an evaluation tool. Do not submit classified, export-controlled, customer-confidential, or otherwise restricted designs to this repository or an unapproved hosted environment.

## Assets to protect

| Asset | Examples | Security objective |
|---|---|---|
| Design IP | RTL, testbenches, gate-level netlists, GDS/OASIS, constraints | Confidentiality, integrity, tenant isolation |
| Process collateral | PDKs, Liberty libraries, technology files, DRC/LVS decks | Integrity, licence compliance, controlled access |
| Verification evidence | Raw logs, reports, waveforms, synthesized outputs, hashes | Integrity, provenance, confidentiality |
| Credentials | API tokens, signing keys, service credentials | Confidentiality, least privilege, rotation |
| Control plane | User identity, authorization decisions, job state, configuration | Integrity, availability, auditability |
| Audit trail | Actor, action, outcome, resource and event-chain metadata | Integrity, retention, traceability |
| Worker host | OS, EDA executables, temporary workspace, process environment | Isolation, availability, recoverability |

## Trust boundaries

1. **Upload/API → intake service:** Treat filenames, archive entries, metadata, and all uploaded bytes as untrusted.
2. **Intake → job controller/queue:** Validate identity, authorization, quotas, allowed job types, and immutable job parameters. Never trust a client-supplied role or tenant identifier without server-side verification.
3. **Controller → worker:** Pass a bounded, validated job specification, not arbitrary shell text. Worker credentials and filesystem access must be scoped to one job.
4. **Worker → EDA tools:** Treat design files, user testbenches, formal tasks, and supplied rule decks as potentially executable or adversarial inputs. EDA tools and scripts may contain vulnerabilities or run arbitrary code.
5. **Worker → artifact store:** Only publish artifacts from the assigned job after validation. Keep raw logs and intermediate files private by default.
6. **Audit writer → audit storage:** Local hash chaining can reveal some edits but cannot stop a privileged actor from deleting, truncating, or replacing the entire log. Production needs independently controlled remote retention.

## Threat scenarios and required controls

| Threat | Required control before customer deployment | Current repository position |
|---|---|---|
| ZIP path traversal, symlink or archive abuse | Reject traversal and unsafe entries; cap compressed/uncompressed size, file count and nesting; extract into a fresh private workspace | Safe extraction exists; validate it against an explicit adversarial archive suite and service deployment |
| Malicious RTL, testbench, SBY task, Tcl/Python/Ruby deck | Run untrusted jobs in a disposable isolated worker with no host secrets, restricted syscalls/capabilities and strict resource limits | The local engine launches tools as subprocesses; this alone is not a sandbox |
| Cross-job or cross-tenant file access | Unique OS identity or equivalent isolation per job; private workspace and artifact namespace; no shared writable directories | Not established by the helper library |
| Network exfiltration or remote payload retrieval | Deny worker network egress by default; allow only explicitly required, controlled endpoints during image/build preparation | Not enforced by current local engine |
| Fork bomb, runaway tool, huge output or disk exhaustion | CPU, memory, process-count, wall-time, output-size, file-size and disk quotas; kill the entire process tree on timeout | POSIX timeout handling now starts a new process session and kills its process group; this is regression-tested, but output/resource quotas and a hostile-worker sandbox remain unimplemented |
| Credential leakage in logs or command lines | Do not place secrets in argv; use scoped short-lived credentials; redact logs; test known and unknown leakage paths | Best-effort common-pattern redaction exists; it is not a guarantee |
| Audit tampering or rollback | Remote append-only/WORM storage, independent permissions, monitoring and retention policy | Local SHA-256 event chain detects some changes but cannot prevent whole-log replacement |
| Unauthorized operation or privilege escalation | Authenticate users; enforce server-side tenant/role/action policy; least-privileged service accounts; review admin paths | Role/action helper is an authorization primitive, not authentication or tenant isolation |
| Compromised dependency/toolchain | Pin versions and hashes, maintain an SBOM, scan dependencies/images, review advisories and sign release artifacts | CI pins selected toolchain components; a complete SBOM/signing/release process is not established |
| Misleading engineering verdict | Preserve raw evidence and tool versions; fail closed on missing prerequisites; use BLOCKED/INCONCLUSIVE/NOT RUN accurately; independent review for sign-off | Explicit statuses and selected regression evidence exist; each flow still needs domain-specific validation |

## Minimum worker deployment contract

A production worker must not be considered ready until all of the following are implemented and tested:

- Disposable per-job VM or hardened container with a non-root identity, read-only base filesystem, and narrowly scoped writable job and scratch directories.
- No privileged mode, host PID/network namespaces, host Docker socket, host home directory, SSH agent, cloud metadata access, or inherited service credentials.
- Default-deny network egress and no runtime dependency downloads during customer jobs.
- CPU, memory, process-count, file-size, disk, and log-output limits. POSIX timeout handling now attempts to terminate the process group, and subprocess output capture is capped at 5 MiB; both behaviors have regression tests. These application-level controls do not replace OS-level resource quotas or verification that descendants cannot escape the worker boundary.
- Allowlisted tool entry points and structured argument arrays; no shell interpolation of user-controlled strings.
- Private artifact namespace per job; validated output paths; controlled export of only approved evidence.
- Immutable worker image reference, pinned tool versions, image/dependency provenance, patch process, and vulnerability response procedure.
- Authenticated control-plane requests, server-side authorization, per-tenant quotas, and independently protected audit storage.
- Security tests for malicious archives, path/symlink escape, process timeout/tree cleanup, output flooding, cross-job access, network denial, and secret non-disclosure.

A Dockerfile or shell wrapper alone does not satisfy this contract. Isolation strength depends on the host kernel/runtime configuration and must be assessed in the target deployment.

## Residual risks and engineering decision

- EDA tools are complex native applications; malformed inputs may trigger tool defects even when the orchestration code is correct.
- PDK and rule-deck licences may constrain storage, redistribution, or execution location.
- Hashes establish identity of observed bytes, not correctness of the design or trustworthiness of a tool.
- A clean software regression does not establish timing closure, foundry sign-off, silicon correctness, defence certification, or fabrication readiness.
- Security-sensitive deployments require a documented data classification, customer-approved architecture, independent review, penetration testing, incident response, and applicable legal/compliance assessment.

## Exit criteria for the worker-isolation milestone

1. A threat-model review is recorded and residual risks have named owners.
2. Worker image/runtime policy is implemented in deployment configuration, not merely documented.
3. Adversarial worker tests demonstrate filesystem isolation, egress denial, bounded resource use and process-tree cleanup.
4. CI runs the security tests and preserves their evidence.
5. A deployment-specific security review is complete before confidential customer designs are accepted.
