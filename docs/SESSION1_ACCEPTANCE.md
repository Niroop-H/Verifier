# Session 1 EDA acceptance criteria

This file defines exit criteria; it is not evidence that they have already passed.

## Required tool stages
1. RTL static analysis: Verilator and/or Icarus parser.
2. RTL compile and simulation: Icarus + VVP on a known-good and known-bad fixture, and at least one self-checking testbench.
3. Synthesis: Yosys elaboration, hierarchy check, process lowering, and statistics.
4. Formal: SBY with solver selected by the task; positive and negative assertions; explicitly distinguish BMC from induction/proof.
5. VHDL: GHDL analyzes a valid fixture and rejects an intentionally invalid fixture.
6. Timing: OpenSTA executes against an actual gate-level netlist, SDC constraints, and compatible Liberty; version-only smoke test is insufficient.
7. DRC/LVS: KLayout executes correct deck(s) on known-good and known-bad layout fixtures, with rule deck and PDK hashes recorded.
8. Regression summary is fail-closed: required BLOCKED/NOT RUN/ERROR cannot be summarized as PASS.
9. Evidence report includes commands, tool versions, input hashes, exit codes, logs, test status, prerequisites and timestamp.
10. Licensing notices and source attribution are preserved.

## Exit gate
Close Session 1 only when required acceptance tests pass on the declared supported toolchain, or explicitly classify any deployment-dependent test as a release blocker. CI green on only a smoke subset does not establish foundry sign-off or fabrication readiness.
