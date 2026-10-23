# MAH Quantum Verify — Technical Evaluation Report
## Session 1: EDA Verification Foundation

**Prepared by:** MAH Quantum  
**Purpose:** Prospective customer / technical evaluator review  
**Evidence date:** 23 October 2026  
**Evidence commit:** `71bf98c1cc9b9843255ceb90390d6bf7d53f8780`  
**CI run:** [EDA Session 1 CI — successful](https://github.com/Niroop-H/Verifier/actions/runs/39904891080)  
**Repository:** https://github.com/Niroop-H/Verifier

---

## 1. Executive summary

MAH Quantum Verify is an early-stage EDA verification orchestration foundation. Session 1 focused on repeatable Linux execution, regression testing selected open-source EDA tools, and producing evidence for engineering review.

The cited GitHub Actions run completed with **3 of 3 jobs successful**:
- Python tests and source checks
- Real EDA toolchain regression
- Official IHP SG13G2 DRC golden regression

This supports a bounded conclusion: the current repository passed its defined Session 1 CI gate. It does not establish that every feature, PDK, design class, or customer environment is validated.

## 2. Scope and evidence

This was an automated repository/CI evaluation, not an independent audit, customer acceptance test, security assessment, foundry qualification, silicon test, or certification exercise.

| Area | Demonstrated in regression | Boundary |
|---|---|---|
| RTL lint | Verilator clean and intentionally defective examples | Does not prove design correctness |
| Verilog simulation | Icarus Verilog/VVP and a self-checking testbench | Depends on testbench coverage |
| Synthesis | Yosys synthesis and structural checks | Not physical implementation sign-off |
| VHDL | GHDL valid/invalid input checks | Not complete mixed-language verification |
| Formal | SymbiYosys proof and counterexample fixtures | Applies only to supplied properties, assumptions and models |
| Static timing | OpenSTA with gate-level netlist, Liberty library and SDC fixtures | Not sign-off for arbitrary designs/corners |
| Generic DRC | KLayout positive/negative smoke fixtures with report parsing | Does not qualify every rule deck |
| PDK-specific DRC | IHP SG13G2 Activ-table golden regression | Specific regression, not full PDK qualification |
| Evidence | CI logs/artifacts and structured report path | Completeness depends on the executed flow and inputs |

### CI outcome

| Job | Result |
|---|---|
| Python tests and source checks | **Success** |
| Real EDA toolchain regression | **Success** |
| Official IHP SG13G2 DRC golden regression | **Success** |

Review the [full CI run and artifacts](https://github.com/Niroop-H/Verifier/actions/runs/39904891080), rather than relying solely on the green status indicator.

## 3. Current implementation areas

The repository provides a local Python execution core and selected adapters for:
- Runtime discovery of installed tools and a tool catalogue.
- Controlled ZIP extraction with path-traversal and archive-size protections.
- RTL lint, simulation/testbench execution and Yosys synthesis checks.
- User-supplied SymbiYosys formal tasks and VHDL analysis.
- OpenSTA timing when netlist, Liberty and SDC inputs are provided.
- KLayout DRC execution with an explicit report-file contract.
- PDK collateral inspection and integration-state catalogue.
- Explicit result statuses, input inventory/hashes, tool versions, logs and JSON/HTML evidence outputs where produced.

These are current implementation/test paths, not a claim that every tool is installed or every integration is production-validated.

## 4. Result semantics

The platform distinguishes PASS, FAIL, BLOCKED, INCONCLUSIVE, NOT RUN and ERROR. Evaluators should confirm:
- PASS applies only to the named check and exact inputs.
- Missing tools, libraries, rule decks or prerequisites do not silently become PASS.
- NOT RUN means the flow was not executed.
- BLOCKED means required prerequisites or configuration are unavailable.
- A process exit code alone does not prove zero DRC violations; inspect the parsed report.
- Raw logs and summaries are reviewed together.

## 5. PDK and sign-off boundaries

A catalogue entry or PDK repository is not evidence of validated DRC/LVS or foundry approval. Customer PDK evaluation requires the exact process release, authorized collateral, technology/layer mapping, compatible tool versions, validated rule decks, known-good references, positive/negative tests, report parsing and written acceptance criteria.

The cited IHP golden regression demonstrates one specific DRC path. It must not be described as full foundry sign-off. No general claim of LVS qualification is made by this report.

## 6. Exclusions from this evaluation

The successful Session 1 run does not demonstrate:
- Universal verification of arbitrary processors, RTL, IP or SoCs.
- Complete CDC/RDC, hardware Trojan detection, side-channel analysis, fault injection, MBIST/LBIST or supply-chain assurance.
- Universal or foundry-qualified DRC/LVS across all catalogued PDKs.
- Wafer inspection, ATE, PUF enrollment, radiation/SEE or thermal testing.
- Production-scale multi-tenant hosting, a customer-approved classified environment or validated air-gapped deployment.
- FIPS, CMMC, FedRAMP, DoD impact-level, ITAR/EAR, DO-254, MIL-STD-883 or MIL-PRF-38535 certification/compliance.
- A conclusion that a design is ready for fabrication or suitable for a particular operational mission.

Such claims require additional implementation and evidence, and may require licensed specialist software, authorized process collateral, physical facilities, independent assessors and customer-specific processes.

## 7. Recommended customer evaluation

### Phase A — Reproduce baseline
1. Review the source and prerequisites.
2. Run the Python checks and sample project on clean Linux.
3. Inspect CI logs and artifacts.
4. Confirm negative fixtures are detected and unavailable flows do not silently pass.

### Phase B — Customer sample
1. Agree on a non-sensitive RTL/VHDL design, testbench and expected outcomes.
2. Define required tools, libraries, constraints and target PDK.
3. Record exact input hashes, versions, commands and expected results.
4. Compare raw logs and platform summaries with an engineer-reviewed baseline.

### Phase C — Acceptance review
1. Classify requirements as demonstrated, partially demonstrated, blocked or out of scope.
2. Review false positives/negatives, repeatability and report completeness.
3. Agree on gaps, remediation owners and acceptance thresholds before production or defence workloads are considered.

Do not upload classified, export-controlled, customer-confidential or restricted designs to the public repository or an unapproved hosted environment.

## 8. Evaluation checklist

- [ ] Source commit and CI run match the evaluation build.
- [ ] Tool versions and dependencies are documented.
- [ ] Sample project completes in a clean environment.
- [ ] Negative tests fail for the intended reason.
- [ ] JSON/HTML reports and raw logs are available for review.
- [ ] Result states are interpreted correctly.
- [ ] PDK and licensed-tool prerequisites are explicitly confirmed.
- [ ] Customer-specific acceptance criteria are agreed in writing.
- [ ] Security/data-handling approval is completed before sensitive design data is used.

## 9. Conclusion

**Session 1 passed its defined automated CI release gate on 23 October 2026.** Evidence supports a functioning and regression-tested foundation for selected EDA workflows, including one specific IHP SG13G2 DRC golden regression.

The recommended next step is a scoped technical evaluation with documented requirements, authorized collateral, known-good sample inputs and customer-reviewed acceptance criteria. Broader production, defence, foundry sign-off or fabrication-readiness claims require additional implementation, validation and independent evidence.

---

*This report describes the current engineering evaluation build and the specific CI evidence linked above. It is not a certification, warranty, independent audit, foundry approval or guarantee of suitability for a particular design or mission.*
