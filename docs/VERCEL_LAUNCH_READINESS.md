# Vercel launch readiness — MAH Quantum Verify

## What this configuration deploys

The repository root contains a static engineering overview at `index.html`. The Vercel configuration in this branch deploys that static site and adds baseline browser security headers. It does **not** deploy the Python EDA engine as a remote execution service.

## Critical product boundary

Do not present this static site as the hosted RTL verification application. The existing Python package is a local EDA orchestration CLI; its native tools must be installed on a supported worker host. The repository's isolated Docker runner is explicitly a deployment prototype, not a production worker service.

A hosted verifier still needs, at minimum:

1. An authenticated API with tenant/project ownership checks.
2. A bounded upload service that safely unpacks and validates project archives.
3. A durable queue and worker supervisor with cancellation and cleanup.
4. A dedicated Linux worker image with pinned tools, image digests and validated licenses/notices.
5. An isolated execution host tested against the acceptance checklist in `WORKER_ISOLATION_DEPLOYMENT.md`.
6. Private artifact/report storage with authorization on every read and download.
7. Durable audit events, retention controls, rate limits and per-user resource quotas.
8. Browser UI wired to real API results; no fabricated progress, metrics, or PASS results.
9. End-to-end tests against the actual deployed API and worker, including malicious input and cancellation.
10. A rollback procedure and monitored health checks.

## Vercel setup

- Import this repository into Vercel.
- Select the branch you intend to deploy.
- Use the repository root as the project root.
- No build command is required for the static overview; Vercel serves `index.html` and repository documents.
- Do not add admin credentials, worker tokens, private keys, or signing keys to client-side variables or static files.

## Release recommendation

This branch is a safe **static-site deployment candidate**, not a production hosted-verifier release. Do not announce remote RTL execution, fabrication readiness, or production isolation until the API and worker requirements above are implemented and the deployment acceptance tests pass.

For local verification, use the existing CLI and the documented fixtures in the repository. A successful local or CI run is evidence for that specific flow only; it is not proof that a remote hosted service is deployed.
