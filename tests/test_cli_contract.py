import json

from mqv_eda.cli import build_parser, main
from mqv_eda.contracts import cli_contract


def test_cli_parser_registers_new_commands():
    parser = build_parser()
    help_text = parser.format_help()
    for command in ("inventory", "run-identity", "repro-check", "baseline-freshness", "license-inventory", "sign-provenance", "verify-provenance-signature", "approvals", "history-dashboard", "policy", "sbom", "flaky",
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



def test_provenance_signing_commands_use_detached_signature_helpers(tmp_path, monkeypatch, capsys):
    from mqv_eda import cli

    provenance = tmp_path / "provenance.json"
    provenance.write_text("{}")
    key = tmp_path / "key.pem"
    signature = tmp_path / "provenance.sig"
    monkeypatch.setattr(cli, "sign_bundle", lambda artifact, private_key, sig: {
        "bundle_sha256": "a" * 64, "signature": str(sig)
    })
    monkeypatch.setattr(cli, "verify_bundle_signature", lambda artifact, public_key, sig: {
        "valid": True, "bundle_sha256": "a" * 64
    })
    assert main(["sign-provenance", str(provenance), "--private-key", str(key),
                 "--signature", str(signature)]) == 0
    signed = json.loads(capsys.readouterr().out)
    assert signed["signed_artifact"] == "provenance"
    assert main(["verify-provenance-signature", str(provenance), "--public-key", str(key),
                 "--signature", str(signature)]) == 0
    verified = json.loads(capsys.readouterr().out)
    assert verified["valid"] is True
    assert verified["verified_artifact"] == "provenance"



def test_approval_cli_blocks_self_approval(tmp_path, capsys):
    db = tmp_path / "approvals.sqlite3"
    code = main([
        "approvals", "--db", str(db), "create",
        "--run-id", "run-1", "--report-sha256", "a" * 64,
        "--actor", "operator", "--role", "release-reviewer",
        "--decision", "APPROVE", "--rationale", "reviewed",
        "--run-operator", "operator",
    ])
    result = json.loads(capsys.readouterr().out)
    assert code == 2
    assert result["status"] == "BLOCKED"



def test_history_dashboard_cli_generates_accessible_html(tmp_path, capsys):
    first = tmp_path / "run-1.json"
    second = tmp_path / "run-2.json"
    first.write_text(json.dumps({"overall_status": "PASS", "checks": [
        {"stage": "lint", "status": "PASS", "duration_seconds": 1.25}
    ]}))
    second.write_text(json.dumps({"overall_status": "FAIL", "checks": [
        {"stage": "simulation", "status": "FAIL", "duration_seconds": 2.5}
    ]}))
    output = tmp_path / "dashboard.html"
    assert main(["history-dashboard", str(first), str(second), "--out", str(output)]) == 0
    capsys.readouterr()
    html = output.read_text()
    assert '<html lang="en">' in html
    assert "Regression Dashboard" in html
    assert 'scope="col"' in html and 'scope="row"' in html
    assert "run-1.json" in html and "run-2.json" in html
    assert "not sign-off" in html
