import hashlib
import json
import time

from mqv_eda.cli import main


def test_waiver_cli_create_list_revoke(tmp_path, capsys):
    db = tmp_path / "governance.sqlite3"
    scope = tmp_path / "scope.json"
    scope.write_text(json.dumps({"project": "adder", "branch": "release"}))
    assert main([
        "waivers", "--db", str(db), "create", "--rule-id", "coverage.minimum",
        "--scope", str(scope), "--reason", "Temporary vendor coverage exception",
        "--created-by", "reviewer", "--expires-at", str(time.time() + 3600),
    ]) == 0
    created = json.loads(capsys.readouterr().out)
    waiver_id = created["id"]
    assert created["status"] == "ACTIVE"
    assert main(["waivers", "--db", str(db), "list"]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert listed["waivers"][0]["id"] == waiver_id
    assert main(["waivers", "--db", str(db), "revoke", waiver_id,
                 "--actor", "reviewer", "--reason", "Exception no longer needed"]) == 0
    revoked = json.loads(capsys.readouterr().out)
    assert revoked["status"] == "REVOKED"


def test_retention_cli_defaults_to_dry_run(tmp_path, capsys):
    target = tmp_path / "evidence.txt"
    target.write_text("preserve me")
    output = tmp_path / "retention.json"
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    assert main([
        "retention-record", str(target), "--action", "delete",
        "--reason", "Retention review", "--actor", "operator",
        "--confirm-sha256", digest, "--out", str(output),
    ]) == 0
    result = json.loads(output.read_text())
    capsys.readouterr()
    assert result["status"] == "WOULD_DELETE"
    assert target.exists()
