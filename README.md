# MAH Quantum Verify
## Engineering Evaluation Release — Session 1: EDA Verification

**Developer:** MAH Quantum  
**Release status:** Engineering evaluation build  
**Evidence commit:** `71bf98c1cc9b9843255ceb90390d6bf7d53f8780`  
**Latest CI evidence:** [Successful three-job GitHub Actions run](https://github.com/Niroop-H/Verifier/actions/runs/39909995640)

MAH Quantum Verify is an early-stage EDA verification orchestration platform. This evaluation release integrates selected open-source tools, runs repeatable sample checks, and packages evidence for engineering review. It is intended for technical evaluation using **non-sensitive sample designs**.

> **Scope boundary:** This is not a claim of universal chip verification, foundry sign-off, defence certification, or fabrication readiness.

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

## Quick start

On Linux with Python 3:

```bash
python3 -m pip install -r requirements-dev.txt
python -m mqv_eda doctor
python -m mqv_eda tool-catalog
python -m mqv_eda pdks
python -m mqv_eda verify fixtures/projects/good --top comb --testbench tb_comb.v --sim-top tb_comb --out build/demo
```

EDA executables must be installed and available on PATH for their corresponding flows. See [Linux build instructions](docs/BUILD_LINUX.md) and `python -m mqv_eda --help` for current options.

## Evidence comparison and failure triage

Compare two JSON reports and write a machine-readable regression summary:

```bash
python -m mqv_eda compare baseline/report.json candidate/report.json --out build/regression.json
```

A newly failing check or a removed baseline check returns exit code 1; malformed reports return 2. Review the output before drawing engineering conclusions.

Analyze a tool log using deterministic, evidence-linked patterns:

```bash
python -m mqv_eda triage build/demo/logs/RTL_COMPILE.log --out build/triage.json
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
