# Session 1 acceptance criteria

## Result semantics

| Status | Meaning |
|---|---|
| PASS | The named check executed and met the named criterion. |
| FAIL | The check executed and detected a violation or exited nonzero. |
| BLOCKED | Required input, tool, library or deck is missing. |
| INCONCLUSIVE | Timeout or incomplete evidence prevents a verdict. |
| NOT RUN | Explicitly excluded by policy or configuration. |
| ERROR | Adapter or infrastructure error. Never convert this to PASS. |

## Automated regression gates

1. Icarus: compile and execute a deterministic testbench; it must print MQV_SIM_PASS.
2. Negative RTL: malformed HDL must return nonzero.
3. Verilator: lint the same synthesizable ALU.
4. Yosys: check hierarchy, processes and synthesize the ALU.
5. GHDL: analyze and elaborate the VHDL fixture.
6. Z3: execute an SMT query and return unsat.
7. SymbiYosys: prove a tautology using the real configured Yosys/Z3 flow.
8. KLayout: run headless and create a synthetic GDS fixture. This is tool-plumbing only, not foundry DRC.
9. OpenSTA: pass the timing fixture before timing is marked integrated. Tool presence alone is insufficient.
10. PDK physical flows must be run with a named authorized PDK revision/deck and positive/negative fixtures before status advances beyond configured.

## Evidence package

- Source revision and CI run identifier.
- Tool paths and version-probe output.
- JUnit XML and detailed test log.
- Per-check status, command, elapsed time, output summary and input hashes.
- Known limitations, skipped-test reasons and license notes.

## Claims not permitted

A smoke test is not full-chip verification, foundry sign-off, certification or fabrication approval. Timing must disclose constraints, Liberty file, corner and parasitic annotation status. DRC/LVS must name the exact deck and PDK revision used.
