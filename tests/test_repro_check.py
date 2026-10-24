import json

from mqv_eda import cli
from mqv_eda.models import CheckResult, Status


def test_repro_check_executes_repeated_runs_and_writes_evidence(tmp_path, monkeypatch, capsys):
    source = tmp_path / "rtl"
    source.mkdir()
    (source / "top.v").write_text("module top; endmodule\n")
    output = tmp_path / "repro"
    calls = {"count": 0}

    def fake_run(*args, **kwargs):
        calls["count"] += 1
        return [CheckResult("lint", Status.PASS, "No issues", required=True, exit_code=0)]

    monkeypatch.setattr(cli, "run_project", fake_run)
    monkeypatch.setattr(cli, "discover_tools", lambda: {
        "platform": "test", "python": "3.test", "tools": {}
    })
    code = cli.main(["repro-check", str(source), "--runs", "3", "--out", str(output)])
    capsys.readouterr()
    summary = json.loads((output / "reproducibility-summary.json").read_text())
    assert code == 0
    assert calls["count"] == 3
    assert summary["status"] == "REPRODUCIBLE_OUTCOME"
    assert summary["input_fingerprint_stable"] is True
    assert all((output / f"run-{i:02d}" / "provenance.json").exists() for i in range(1, 4))


def test_repro_check_flags_different_outcomes(tmp_path, monkeypatch, capsys):
    source = tmp_path / "rtl"
    source.mkdir()
    (source / "top.v").write_text("module top; endmodule\n")
    output = tmp_path / "repro"
    calls = {"count": 0}

    def fake_run(*args, **kwargs):
        calls["count"] += 1
        status = Status.PASS if calls["count"] == 1 else Status.FAIL
        return [CheckResult("simulation", status, "Outcome", required=True, exit_code=0)]

    monkeypatch.setattr(cli, "run_project", fake_run)
    monkeypatch.setattr(cli, "discover_tools", lambda: {
        "platform": "test", "python": "3.test", "tools": {}
    })
    code = cli.main(["repro-check", str(source), "--runs", "2", "--out", str(output)])
    capsys.readouterr()
    summary = json.loads((output / "reproducibility-summary.json").read_text())
    assert code == 1
    assert summary["status"] == "NONDETERMINISTIC_OUTCOME"
