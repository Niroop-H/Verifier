# End-to-end semiconductor verification coverage matrix

## Purpose

MQV is intended to orchestrate evidence-backed checks across the semiconductor lifecycle, from RTL through physical sign-off and post-silicon qualification. This document defines the coverage target and separates current integrations from planned units. The catalogue in `mqv_eda/verification_catalog.py` is machine-readable; its `integration` field is not a claim that a unit has run on a submitted design.

## Verification domains

| Domain | Verification units | Key inputs and evidence |
|---|---|---|
| Front end | RTL lint, elaboration, hierarchy, language analysis | RTL, include paths, defines, tool versions, lint/elaboration logs |
| Functional | RTL simulation, directed/random regression, assertions, functional/code coverage | Testbench, reference model, assertions, seeds, coverage model, regression summaries |
| Formal | Property proof, bounded/unbounded proofs where supported, counterexamples, RTL-to-netlist equivalence | Properties, assumptions, reset/clock model, reference and candidate representations, proof logs |
| Clock/reset | CDC, RDC, synchronizer/reconvergence and reset-release checks | Clock/reset intent, constraints, waivers and review rationale |
| Testability | DFT rule checks, scan architecture, ATPG/fault coverage, test-mode checks | DFT intent, libraries, scan rules, ATPG setup and pattern reports |
| Logic implementation | Synthesis, structural checks, area/resource estimates, netlist validation | RTL, synthesis constraints, libraries, generated netlist and logs |
| Power/performance | Dynamic/leakage power, activity quality, performance targets | Netlist, Liberty, activity data, power intent and operating corners |
| Timing | Setup/hold, recovery/removal, clock-gating, unconstrained paths, clock quality, SI/crosstalk | Netlist, SDC, libraries, parasitics, corners and exception review |
| Physical design | Floorplan, placement, CTS, routing, congestion, parasitic extraction | Netlist, floorplan, technology/cell LEF, process rules, extracted RC |
| Physical sign-off | DRC, LVS, ERC, antenna and process-specific checks | Exact PDK release, layout, reference netlist, authorized rule decks, maps and waivers |
| Reliability | EM/IR-drop, thermal and operating-envelope analysis | Routed layout, power/current models, process reliability limits, package/thermal models |
| Assurance | Hardware security review, configuration/provenance, requirements traceability, waiver governance | Threat model, security requirements, toolchain/input hashes, signed review evidence |
| Silicon | Post-silicon validation, ATE, characterization, environmental/reliability qualification | Fabricated samples, lab/ATE setup, test plans, limits and measured results |

## Result semantics and readiness gate

Every unit must report one of `PASS`, `FAIL`, `BLOCKED`, `INCONCLUSIVE`, `NOT RUN`, or `ERROR`. A missing prerequisite is never a pass. Each result should retain the exact input hashes, tool and version, command/configuration, constraints/corners, logs, generated evidence, timestamps and reviewed waivers.

MQV must not issue a generic `FABRICATION READY` verdict from RTL lint, compilation, synthesis, or a checklist alone. A readiness assessment is meaningful only for a declared target process and scope, and must identify all mandatory criteria and accepted waivers. It must require appropriate functional/formal evidence, implementation and equivalence checks, timing/power sign-off, physical DRC/LVS/ERC and reliability sign-off where applicable, plus human sign-off by the responsible design/foundry team. Missing evidence yields `INCOMPLETE`/`BLOCKED`, not PASS. Software-only analysis cannot establish silicon characterization, ATE results or qualification before silicon exists.

## Example: Intel Core Ultra-class CPU

A commercial Intel Core Ultra-class processor is not a realistic drop-in validation target for an external tool without the complete authorized design collateral. Its RTL/netlists, microarchitecture implementation, internal verification environment, process-specific libraries/PDK, sign-off decks and constraints are proprietary and not generally available. MQV can support an authorized design only when those inputs and licensed tools are supplied by the rights holder; it cannot infer or recreate Intel's internal sign-off process from public information or a processor name.

For large SoCs, verification also needs partitioned and hierarchical execution, resource/time budgets, incremental runs, reproducible caches, waiver ownership, coverage closure tracking, multi-corner/multi-mode timing, IP/subsystem integration evidence, and controlled access to licensed collateral. These are product-level engineering milestones, not a single command or model response.

## Current implementation maturity

`IMPLEMENTED` means a supported flow exists in the current repository; it does not mean every input configuration or production use is validated. `CATALOG_ONLY` means the unit is a planned coverage target and is not yet a complete runnable MQV integration. `EXTERNAL_EVIDENCE` means the evidence comes from physical silicon/lab/ATE or another controlled external process. Check current code, integration tests and raw reports before claiming support.

## Immediate implementation priorities

1. Convert the catalogue into a dependency-aware run plan with explicit prerequisites and non-bypassable status semantics.
2. Add tests for missing constraints/libraries/decks, invalid configuration, and fail-closed aggregation.
3. Expand reference designs beyond tiny combinational examples: CPU core with testbench, bus/IP blocks, cache/controller, and eventually subsystem-level designs with coverage models.
4. Add validated CDC/RDC and equivalence integrations, then power/physical sign-off integrations only where licensed tools and valid collateral are available.
5. Add readiness reports that distinguish design correctness, timing closure, physical sign-off, security/reliability review, and external silicon qualification.

Do not use confidential or restricted commercial RTL, netlists, PDKs, or rule decks in a public repository or unapproved hosted runner. Confirm licences and access controls before using customer or foundry collateral.
