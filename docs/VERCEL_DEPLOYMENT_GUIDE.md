# Vercel deployment guide — MAH Quantum Verify

This guide deploys the repository's existing white, static engineering overview. It does not deploy the Python EDA execution engine as a serverless service.

## Deploy the static site

1. Open Vercel and choose **Add New → Project**.
2. Import `Niroop-H/Verifier`.
3. Select branch `launch/hosted-verifier-candidate` for the candidate preview. Do not change the production branch until review is complete.
4. Set **Root Directory** to `./`.
5. Framework preset: **Other**.
6. Build command: leave empty.
7. Output directory: leave empty / default (repository root).
8. Deploy.
9. Open the deployment and verify the homepage and links to `docs/TOOL_INTEGRATION_MATRIX.md`, `docs/BUILD_LINUX.md`, and `docs/OPEN_PDK_SUPPORT.md`.

The `vercel.json` file sets clean URLs and baseline response headers. This is a static deployment; it has no login system, job API, upload processing, or remote EDA execution.

## Do not configure fake credentials

Do not put admin passwords, worker secrets, signing keys, or customer credentials into static environment variables or browser code. Vercel environment variables exposed to client-side code are not secret.

## Hosted verifier prerequisites

To launch upload-and-run functionality, deploy a separate authenticated API and dedicated Linux worker with the required EDA tools. Then configure a server-side API origin in the web app. The API must enforce authentication and project ownership for every endpoint; uploads need archive validation, quotas, and safe temporary storage; jobs need a durable queue, cancellation, timeout enforcement, cleanup, and private report storage.

The isolated runner described in `docs/WORKER_ISOLATION_DEPLOYMENT.md` is a prototype and must pass that document's acceptance tests on the actual target host before it receives untrusted customer RTL.

## Smoke-check list for the static preview

- [ ] Homepage loads over HTTPS.
- [ ] No secrets appear in page source or deployment logs.
- [ ] All internal documentation links resolve.
- [ ] Browser console has no failed assets or script errors.
- [ ] Security headers are present.
- [ ] Product copy continues to distinguish CI-tested adapters from catalogue-only tools.
- [ ] No UI implies that an RTL run occurred unless a real worker produced the evidence.

## Release status

A successful Vercel deployment validates only the static site. It does not validate or deploy native EDA execution. Keep the hosted verification feature disabled until the API/worker path is implemented and tested end to end.
