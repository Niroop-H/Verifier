import json

from mqv_eda import cli
from mqv_eda.job_queue import enqueue
from mqv_eda.models import CheckResult, Status


def test_run_once_executes_queued_verification_and_persists_evidence(tmp_path, monkeypatch, capsys):
    db = tmp_path / "jobs.sqlite3"
    source = tmp_path / "rtl"
    source.mkdir()
    (source / "top.v").write_text("module top; endmodule\n")
    output = tmp_path / "job-output"
    job = enqueue(db, {"source": str(source), "output_dir": str(output), "top": "top"})
    monkeypatch.setattr(cli, "run_project", lambda *a, **k: [
        CheckResult("lint", Status.PASS, "No issues", required=True)
    ])
    monkeypatch.setattr(cli, "discover_tools", lambda: {
        "platform": "test", "python": "3.test", "tools": {}
    })

    assert cli.main(["jobs", "--db", str(db), "run-once", "--worker-id", "worker-1"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["state"] == "SUCCEEDED"
    assert result["worker_id"] == "worker-1"
    assert (output / "report.json").exists()
    assert json.loads((output / "provenance.json").read_text())["report"]["status"] == "PRESENT"
    report = json.loads((output / "report.json").read_text())
    assert report["metadata"]["job_id"] == job["id"]
    assert report["metadata"]["run_identity"]["input_file_count"] == 1


def test_run_once_reports_idle_when_queue_empty(tmp_path, capsys):
    db = tmp_path / "jobs.sqlite3"
    assert cli.main(["jobs", "--db", str(db), "run-once", "--worker-id", "worker-idle"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["state"] == "IDLE"



def test_run_once_returns_failure_for_nonpassing_verification(tmp_path, monkeypatch, capsys):
    db = tmp_path / "jobs.sqlite3"
    source = tmp_path / "rtl"
    source.mkdir()
    (source / "top.v").write_text("module top; endmodule\n")
    enqueue(db, {"source": str(source), "output_dir": str(tmp_path / "failed-output")})
    monkeypatch.setattr(cli, "run_project", lambda *a, **k: [
        CheckResult("simulation", Status.FAIL, "Mismatch", required=True)
    ])
    monkeypatch.setattr(cli, "discover_tools", lambda: {
        "platform": "test", "python": "3.test", "tools": {}
    })
    assert cli.main(["jobs", "--db", str(db), "run-once", "--worker-id", "worker-fail"]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["state"] == "FAILED"
