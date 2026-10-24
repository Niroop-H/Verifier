"""Versioned public CLI contract metadata."""
from __future__ import annotations

CLI_CONTRACT_VERSION = "1.0"
EXIT_CODES = {
    "0": "Command completed successfully; for policy/approval commands, see the emitted decision state.",
    "1": "A verification failure or regression was detected by commands whose contract defines this outcome.",
    "2": "Invalid input, blocked policy, unavailable prerequisite, or execution error; inspect structured output and stderr.",
}
COMMANDS = {
    "doctor": {"success": 0, "unavailable_toolchain": 2},
    "verify": {"pass": 0, "fail": 1, "blocked_or_error": 2},
    "repro-check": {"stable_outcome": 0, "outcome_variation_or_input_change": 1, "invalid_input_or_error": 2},
    "compare": {"no_regression": 0, "regression": 1, "invalid_input": 2},
    "policy": {"eligible_for_human_review": 0, "blocked": 2},
    "baseline-freshness": {"fresh": 0, "stale_or_unverifiable": 2},
    "license-inventory": {"inventory_written": 0, "invalid_or_error": 2},
    "jobs run-once": {"job_executed": 0, "idle_or_no_queued_job": 0, "execution_error": 2},
    "approval-record": {"approved": 0, "not_approved_or_blocked": 2},
    "bundle": {"verified_or_created": 0, "invalid_or_error": 2},
    "verify-evidence-signature": {"valid": 0, "invalid_or_error": 2},
    "sign-provenance": {"signature_written": 0, "invalid_or_error": 2},
    "verify-provenance-signature": {"valid": 0, "invalid_or_error": 2},
    "golden-corpus": {"valid": 0, "invalid": 2},
}


def cli_contract() -> dict:
    return {
        "contract": "mqv-aegis-cli",
        "contract_version": CLI_CONTRACT_VERSION,
        "exit_codes": EXIT_CODES,
        "command_exit_codes": COMMANDS,
        "compatibility_policy": {
            "patch": "Additive optional fields and new commands only; do not change existing exit meanings.",
            "minor": "Additive features that preserve existing command behavior.",
            "major": "Breaking command syntax, required fields, output meaning, or exit-code semantics.",
        },
        "limitations": [
            "Some legacy commands have historical output formats not yet normalized under a shared envelope.",
            "The contract describes intended behavior; tests must enforce each listed case before a release.",
        ],
    }
