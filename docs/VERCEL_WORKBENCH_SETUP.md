# AEGIS EDA Verifier — Vercel RTL Workbench setup

The tools.html workbench submits a real Icarus Verilog compile and VVP simulation job to GitHub Actions. Vercel serves the interface and API bridge; it does not itself run Icarus.

## One-time Vercel configuration

1. In GitHub, create a fine-grained personal access token for Niroop-H/Verifier.
2. Grant repository permissions:
   - Actions: Read and write
   - Contents: Read-only
3. In Vercel, open the project connected to this repository → Settings → Environment Variables.
4. Add GITHUB_TOKEN with the token value for Production (and Preview if needed). Do not commit the token to the repository or put it in browser JavaScript.
5. Redeploy the latest deployment after saving the environment variable.
6. Open /tools on the deployed site, load RTL and a testbench, and run a simulation.

## What is implemented

- POST /api/verify validates source sizes and module identifiers, then dispatches .github/workflows/aegis-web-simulation.yml.
- GET /api/verify?job_id=... checks the Actions run status.
- The workflow installs Icarus Verilog on a fresh Ubuntu runner, compiles the supplied design and testbench, runs VVP, and uploads logs and result.json as a one-day artifact.
- The page links to the GitHub Actions run where evidence can be inspected and downloaded.

## Limits and security

- This is an initial real RTL simulation workflow, not the full local mqv_eda orchestration engine.
- RTL source limit: 25 KB; testbench limit: 10 KB; runner timeout: 5 minutes.
- Do not upload confidential, export-controlled or customer-restricted designs. Submitted source is sent to GitHub Actions and temporarily processed there.
- A simulator process exiting successfully is not proof of functional correctness. Use self-checking assertions in the testbench; inspect compile and simulation logs.
- No formal proof, synthesis sign-off, STA, DRC/LVS, foundry qualification or fabrication-readiness claim is made by this workbench.
- The API token is privileged. Use a repository-scoped fine-grained token and rotate it if exposed.
