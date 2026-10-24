import json

from mqv_eda.cli import build_parser, main
from mqv_eda.contracts import cli_contract


def test_cli_parser_registers_new_commands():
    parser = build_parser()
    help_text = parser.format_help()
    for command in ("inventory", "run-identity", "baseline-freshness", "license-inventory", "policy", "sbom", "flaky",
                    "cluster-failures", "coverage", "evidence-scorecard", "provenance", "jobs", "history", "minimize-failures", "validate-config",
                    "approval-record", "validate-waiver", "change-impact", "estimate-resources",
                    "cleanup-workspace", "retention-record", "mutation-score", "golden-corpus", "waivers"):
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



def test_baseline_freshness_cli_blocks_stale_baseline(tmp_path, capsys):
    baseline = tmp_path / "baseline.json"
    current = tmp_path / "current.json"
    baseline.write_text(json.dumps({"metadata": {"run_identity": {
        "created_utc": "2020-01-01T00:00:00+00:00", "source_revision": "same"
    }}}))
    current.write_text(json.dumps({"metadata": {"run_identity": {"source_revision": "same"}}}))
    output = tmp_path / "freshness.json"
    code = main(["baseline-freshness", str(baseline), str(current),
                 "--max-age-seconds", "60", "--out", str(output)])
    result = json.loads(output.read_text())
    capsys.readouterr()
    assert code == 2
    assert result["status"] == "STALE_OR_UNVERIFIABLE"



def test_license_inventory_cli_emits_report(tmp_path, capsys):
    root = tmp_path / "source"
    root.mkdir()
    (root / "LICENSE").write_text("SPDX-License-Identifier: Apache-2.0\n")
    output = tmp_path / "license-report.json"
    assert main(["license-inventory", str(root), "--out", str(output)]) == 0
    result = json.loads(output.read_text())
    capsys.readouterr()
    assert result["spdx_declared_count"] == 1
    assert result["files"][0]["spdx_identifiers"] == ["Apache-2.0"]
