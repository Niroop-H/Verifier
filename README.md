# MAH Quantum Verify
## Engineering Evaluation Release — Session 1: EDA Verification

**Developer:** MAH Quantum  
**Release status:** Engineering evaluation build  
**Evidence commit:** `71bf98c1cc9b9843255ceb90390d6bf7d53f8780`  
**Latest CI evidence:** [Successful three-job GitHub Actions run](https://github.com/Niroop-H/Verifier/actions/runs/39909995640)

MAH Quantum Verify is an early-stage EDA verification orchestration platform. This evaluation release integrates selected open-source tools, runs repeatable sample checks, and packages evidence for engineering review. It is intended for technical evaluation using **non-sensitive sample designs**.

> **Scope boundary:** This is not a claim of universal chip verification, foundry sign-off, defence certification, or fabrication readiness.

## Product roadmap — 50 high-value engineering features

The [50-feature engineering backlog](docs/FEATURE_CATALOG_50.md) prioritizes less-visible capabilities that matter in serious verification workflows. See the [live implementation status](docs/FEATURE_IMPLEMENTATION_STATUS.md) for a conservative item-by-item breakdown of implemented baselines, partial work, and remaining acceptance criteria. The roadmap is not a claim that all listed features are production-ready.

## Session 2 — Security assurance foundation

- [Session 2 completion status](docs/SESSION2_COMPLETION_STATUS.md): delivered controls, latest CI evidence, and the explicit production-readiness blockers.

- [Security assurance foundation](docs/SESSION2_SECURITY_ASSURANCE.md): path validation, deny-by-default role/action checks, best-effort secret redaction and hash-chained audit events.
- [Threat model and worker security contract](docs/SESSION2_THREAT_MODEL.md): assets, trust boundaries, attack scenarios, deployment controls and worker-isolation exit criteria.
- [Isolated worker deployment prototype](docs/WORKER_ISOLATION_DEPLOYMENT.md): constrained Docker runner, runtime assumptions and deployment acceptance tests.

These controls are building blocks, not proof of a secure deployment or defence/regulatory authorization. A constrained Docker runner prototype is included, but it must be validated on a dedicated target host and is not yet a production sandbox.

## Session 1 — CI results

The latest cited CI run completed with all three jobs successful:

1. Python tests and source checks
2. Real EDA toolchain regression
3. Official IHP SG13G2 DRC golden regression

The suite exercises selected RTL lint, Verilog simulation, synthesis, VHDL analysis, formal proof/counterexample, static timing and DRC fixtures. Review the [technical evaluation report](docs/EVALUATION_REPORT.md), [acceptance criteria](docs/SESSION1_ACCEPTANCE.md), [tool integration matrix](docs/TOOL_INTEGRATION_MATRIX.md), [open PDK notes](docs/OPEN_PDK_SUPPORT.md), and [toolchain provenance](docs/TOOLCHAIN_PROVENANCE.md).

## Install and quick start

### Install the packaged CLI

Python 3.10 or newer is required. Download the wheel from the successful GitHub Actions run artifact named `mah-quantum-verify-python-distribution`, then install it:

```bash
python -m pip install ./mah_quantum_verify-0.1.0-py3-none-any.whl
mqv-eda --help
mqv-eda doctor
mqv-eda tool-catalog
mqv-eda pdks
```

The wheel contains the MAH Quantum Verify Python application. EDA executables are separate system dependencies and must be installed and available on `PATH` for each relevant flow. The package does not bundle commercial tools or PDK collateral.

### Run the sample project from a source checkout

On Linux with Python 3:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m mqv_eda doctor
python -m mqv_eda tool-catalog
python -m mqv_eda pdks
python -m mqv_eda verify fixtures/projects/good --top comb --testbench tb_comb.v --sim-top tb_comb --out build/demo
```

See [Linux build instructions](docs/BUILD_LINUX.md) and `python -m mqv_eda --help` for current options.

## Detached signatures for evidence bundles

For environments that have OpenSSL available, sign the final ZIP with a separately managed private key:

```bash
python -m mqv_eda sign-evidence build/aegis-evidence.zip --private-key keys/evidence-private.pem --signature build/aegis-evidence.sig
python -m mqv_eda verify-evidence-signature build/aegis-evidence.zip --public-key keys/evidence-public.pem --signature build/aegis-evidence.sig
```

Never commit private keys or place them inside the evidence ZIP. The verifier only establishes signature validity for the supplied public key; the customer must independently trust and pin that key. For production, use an approved key-management process and rotate/revoke keys under documented policy.

## Integrity-checked evidence bundles

Create a ZIP package containing evidence files plus a SHA-256 manifest, then verify its contents after transfer:

```bash
python -m mqv_eda bundle create mqv-report build/aegis-evidence.zip --project demo
python -m mqv_eda bundle verify build/aegis-evidence.zip
```

The verifier checks member paths, manifest membership, file sizes, and file hashes. This detects post-export changes relative to the included manifest; it does not authenticate the publisher because the manifest is unsigned. Do not include restricted or classified data unless the destination and transfer process are approved.

## Evidence comparison and failure triage

Compare two JSON reports and write a machine-readable regression summary:

```bash
python -m mqv_eda compare baseline/report.json candidate/report.json --out build/regression.json
```

A newly failing check or a removed baseline check returns exit code 1; malformed reports return 2. Review the output before drawing engineering conclusions.

Analyze a tool log using deterministic, evidence-linked patterns:

```bash
python -m mqv_eda triage build/demo/logs/RTL_COMPILE.log --out build/triage.json

### Engineering governance and regression workflows

```bash
# Bind a report to input/configuration/toolchain identity and emit provenance
python -m mqv_eda verify fixtures/projects/good --top comb --testbench tb_comb.v --sim-top tb_comb --out build/demo
python -m mqv_eda sign-provenance build/demo/provenance.json --private-key keys/provenance-private.pem --signature build/demo/provenance.sig

# Execute controlled reruns and compare check outcomes
python -m mqv_eda repro-check fixtures/projects/good --runs 3 --top comb --testbench tb_comb.v --sim-top tb_comb --out build/repro

# Review baseline freshness, license notices and historical regressions
python -m mqv_eda baseline-freshness baseline/report.json candidate/report.json --max-age-seconds 604800
python -m mqv_eda license-inventory vendor --out build/license-inventory.json
python -m mqv_eda history-dashboard build/demo/report.json build/repro/run-01/report.json --out build/regression-dashboard.html

# Execute one locally queued verification job
python -m mqv_eda jobs --db .mqv/jobs.sqlite3 submit job-payload.json
python -m mqv_eda jobs --db .mqv/jobs.sqlite3 run-once --worker-id local-worker

# Record a review decision against an exact report digest
python -m mqv_eda approvals --db .mqv/approvals.sqlite3 create --run-id RUN_ID --report-sha256 REPORT_SHA256 --actor REVIEWER --role release-reviewer --decision APPROVE --rationale "Evidence reviewed" --run-operator OPERATOR --policy-author POLICY_AUTHOR
```

These workflows provide local evidence, governance and repeatability controls. They do not authenticate local actor labels, prove bit-for-bit reproducibility, or authorize tape-out/fabrication. Review each command's generated evidence and documented limitations.
```

Triage suggestions are heuristics, not proven root causes. They include matching log lines and hashes so an engineer can inspect the original evidence. Neither command independently validates the underlying EDA result.

## Product differentiation and customer trust

- [Customer choice and competitive advantage backlog](docs/CUSTOMER_CHOICE_AND_COMPETITIVE_ADVANTAGE.md): measurable differentiators, customer value metrics, defence-oriented requirements, and release gates.
- [Differentiation and defence readiness plan](docs/DIFFERENTIATION_AND_DEFENCE_READINESS.md): data custody, security, supply-chain transparency, pilot criteria, and claims boundaries.

These documents describe implementation targets and acceptance criteria. They are not claims that all listed features, security controls, certifications, or defence approvals are already complete.

## Current implementation areas

- Controlled ZIP extraction with traversal and archive-size protections.
- Runtime tool discovery and a catalogue of EDA tools.
- RTL lint, testbench compilation/execution, synthesis and structural checks.
- User-supplied SymbiYosys formal tasks and VHDL analysis.
- OpenSTA timing when a gate-level netlist, Liberty library and SDC are provided.
- KLayout DRC execution with report parsing and positive/negative smoke fixtures.
- PDK collateral inspection and integration-state catalogue.
- Explicit result states: PASS, FAIL, BLOCKED, INCONCLUSIVE, NOT RUN and ERROR.
- Input inventory/hashes, tool versions, logs and structured JSON/HTML evidence where produced by a flow.

## Interpreting results

A **PASS** applies only to the specific configured check and its inputs. Missing tools, libraries, rule decks or other prerequisites must not be treated as success. BLOCKED and NOT RUN indicate that a check could not be evaluated or was not executed; ERROR indicates an execution or reporting problem. Inspect the raw logs and reports, not just the summary.

## PDK, licences and boundaries

The catalogue includes references/profiles for ecosystems such as SKY130, GF180MCU, IHP SG13G2 and ASAP7. A catalogue entry is not proof of validated DRC/LVS or foundry approval. PDK-specific physical verification requires the exact process release, authorized collateral, technology/layer maps, compatible tool versions and validated rule decks.

Commercial simulators, formal engines and emulation platforms require separate licences and authorized installations. Physical silicon tests, wafer inspection, ATE/PUF enrollment, radiation and thermal qualification cannot be established by a software-only CI run.

## Safe evaluation

- Use non-sensitive sample designs for public-repository evaluation.
- Do not upload classified, export-controlled, customer-confidential or restricted design data to this public repository or an unapproved hosted service.
- Review licensing and redistribution rights for tools, PDKs, libraries, rule decks and generated artifacts.
- Treat logs and reports as potentially sensitive.
- A successful CI run is regression evidence, not security certification or customer acceptance.

## Evaluation procedure

1. Read [the technical evaluation report](docs/EVALUATION_REPORT.md).
2. Inspect the [latest successful CI run](https://github.com/Niroop-H/Verifier/actions/runs/39906280785) and its artifacts.
3. Re-run the included sample project in a clean Linux environment.
4. Check both positive and negative test cases and inspect raw reports.
5. Agree on separate customer-specific acceptance criteria before testing any customer design.

**Conclusion:** Session 1 passed its defined automated CI release gate. It establishes a functioning, regression-tested foundation for selected EDA flows—not production sign-off or universal verification.
