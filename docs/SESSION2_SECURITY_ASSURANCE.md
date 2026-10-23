# Session 2 — Security Assurance (foundation)

## Objective
Add testable, fail-closed security primitives while preserving the Session 1 EDA regression gate. This is a security engineering foundation, not a penetration-test clearance, secure deployment, or regulatory certification.

## Implemented in this increment
- Path validation rejects absolute, drive-qualified, traversal and control-character paths; resolved workspace targets are checked against the root.
- Explicit role/action allow-list denies unknown roles and actions by default.
- Best-effort redaction covers common inline token/API-key/password/secret assignments and bearer-token strings.
- Append-only JSONL audit helper records actor, action, outcome, resource ID, timestamp and event SHA-256; new files request owner-only permissions on POSIX systems.
- Regression tests cover traversal, symlink escape, authorization defaults, redaction and audit output/permissions.

## Deployment boundaries
These helpers are not a complete security boundary. They do not provide authentication, MFA, tenant isolation, process/container sandboxing, network egress control, immutable/WORM audit storage, key management, encryption, rate limiting, CSRF protection, signed releases, SBOMs, vulnerability scanning or incident response.

The path resolver cannot by itself eliminate time-of-check/time-of-use races. Use private per-job workspaces, restrictive OS permissions, no untrusted shared writable parents, and OS/container isolation. Authorization must be enforced by trusted server-side code, never only by the UI. Audit records need trusted identity, access controls, retention, tamper-evident external storage and monitoring in production.

Secret redaction is best-effort, not a guarantee that arbitrary secrets or sensitive RTL cannot appear in logs. Do not put credentials in command-line arguments, source files, public issues or sample fixtures. Treat RTL, netlists, constraints, PDK files and reports as potentially customer-confidential.

## Security acceptance gates
1. Unit tests for path handling, authorization defaults, secret redaction and audit structure pass.
2. Existing Session 1 EDA CI remains green.
3. Missing identity/policy never implies authorization; denials are explicit.
4. Controls are verified in the actual service/worker deployment before processing customer designs.
5. Threat model, dependency review, isolated worker design and security test plan are reviewed before customer/defence deployment.

## Not claimed
No claim of FIPS 140-3 validation, CMMC/FedRAMP/DoD IL authorization, ITAR/EAR compliance, penetration-test clearance, zero-trust completion, or suitability for classified data. These require deployment-specific evidence, governance and independent assessment.
