import json

from mqv_eda import cli
from mqv_eda.models import CheckResult, Status


def test_verify_report_persists_run_identity_and_toolchain_snapshot(tmp_path, monkeypatch):
    source = tmp_path / "rtl"
    source.mkdir()
    (source / "top.v").write_text("module top; endmodule\n")
    output = tmp_path / "out"

    monkeypatch.setattr(cli, "run_project", lambda *a, **k: [
        CheckResult("preflight", Status.PASS, "fixture")
    ])
    monkeypatch.setattr(cli, "discover_tools", lambda: {
        "platform": "test-platform", "python": "3.test",
        "tools": {"iverilog": {"state": "AVAILABLE", "version": "test-version"}},
    })

    assert cli.main(["verify", str(source), "--out", str(output)]) == 0
    report = json.loads((output / "report.json").read_text())
    metadata = report["metadata"]
    assert metadata["toolchain_snapshot"]["tools"]["iverilog"]["version"] == "test-version"
    identity = metadata["run_identity"]
    assert identity["input_file_count"] == 1
    assert len(identity["input_fingerprint_sha256"]) == 64
    assert len(identity["run_fingerprint_sha256"]) == 64
    assert identity["configuration"]["timeout_seconds"] > 0
