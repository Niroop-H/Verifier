# Vercel deployment notes

This repository is configured for a **static-site deployment** on Vercel from the `main` branch.

## Vercel project settings

- Git repository: `Niroop-H/Verifier`
- Production branch: `main`
- Framework preset: `Other` (unless Vercel detects a more suitable preset)
- Root directory: repository root
- Build command: leave empty
- Output directory: `.`

Vercel should serve the repository's root `index.html`. If the import wizard shows a build command inherited from an unrelated framework, clear it before deploying.

## Important product boundary

The repository contains a Python-based EDA orchestration package intended for local execution. A static Vercel deployment does **not** execute Icarus Verilog, Verilator, Yosys, or other native EDA tools, and it does not create a remote RTL-verification API or worker. Do not represent the static website as a hosted RTL verification service until an authenticated API, isolated worker, durable job handling, private artifact storage, and end-to-end hosted execution have been deployed and tested.

Keep production credentials out of the repository. Configure secrets only in the hosting environment after the corresponding backend exists.
