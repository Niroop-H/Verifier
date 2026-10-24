import json

from mqv_eda.cli import build_parser, main
from mqv_eda.contracts import cli_contract


def test_cli_parser_registers_new_commands():
    parser = build_parser()
    help_text = parser.format_help()
    for command in ("inventory", "run-identity", "policy", "sbom", "flaky",
                    "cluster-failures", "coverage", "evidence-scorecard", "provenance", "jobs", "history", "minimize-failures", "validate-config",
                    "approval-record", "validate-waiver", "change-impact", "estimate-resources",
                    "cleanup-workspace", "retention-record", "mutation-score", "golden-corpus"):
        assert command in help_text


def test_contract_command_emits_versioned_json(capsys, tmp_path):
    out = tmp_path / "contract.json"
    assert main(["contract", "--out", str(out)]) == 0
    saved = json.loads(out.read_text())
    printed = json.loads(capsys.readouterr().out)
    assert saved["contract_version"] == "1.0"
    assert printed["contract"] == "mqv-aegis-cli"
    assert "major" in saved["compatibility_policy"]


def test_policy_cli_blocks_missing_required_check(tmp_path, capsys):
    report = tmp_path / "report.json"
    policy = tmp_path / "policy.json"
    report.write_text(json.dumps({"checks": []}))
    policy.write_text(json.dumps({"policy_id": "release", "version": "1", "required_checks": ["lint"]}))
    out = tmp_path / "decision.json"
    code = main(["policy", str(report), str(policy), "--out", str(out)])
    assert code == 2
    result = json.loads(out.read_text())
    assert result["decision"] == "BLOCKED"
