import time

import pytest

from mqv_eda.waiver_register import (
    create_waiver, get_waiver, list_waivers, revoke_waiver, waiver_applies,
)


def test_waiver_persists_scope_expiry_and_audit_events(tmp_path):
    db = tmp_path / "governance.sqlite3"
    waiver = create_waiver(
        db, rule_id="coverage.minimum", scope={"project": "adder", "branch": "release"},
        reason="Vendor model coverage is temporarily unavailable.",
        created_by="reviewer-1", expires_at=time.time() + 3600,
    )
    assert waiver["status"] == "ACTIVE"
    assert waiver_applies(waiver, rule_id="coverage.minimum",
                          context={"project": "adder", "branch": "release"})
    assert not waiver_applies(waiver, rule_id="coverage.minimum",
                              context={"project": "adder", "branch": "main"})
    persisted = get_waiver(db, waiver["id"])
    assert persisted["scope"] == {"branch": "release", "project": "adder"}
    assert persisted["events"][0]["action"] == "CREATED"
    assert list_waivers(db)[0]["id"] == waiver["id"]


def test_revoke_is_durable_and_disables_waiver(tmp_path):
    db = tmp_path / "governance.sqlite3"
    waiver = create_waiver(db, rule_id="rule-1", scope={"project": "x"},
                           reason="Temporary documented exception.",
                           created_by="alice", expires_at=time.time() + 3600)
    revoked = revoke_waiver(db, waiver["id"], actor="bob", reason="Risk resolved")
    assert revoked["status"] == "REVOKED"
    assert revoked["revoked_by"] == "bob"
    assert revoked["events"][-1]["action"] == "REVOKED"
    assert not waiver_applies(revoked, rule_id="rule-1", context={"project": "x"})
    with pytest.raises(ValueError, match="only an unexpired active"):
        revoke_waiver(db, waiver["id"], actor="bob", reason="Duplicate revoke")


def test_invalid_waiver_inputs_and_expired_waiver_fail_closed(tmp_path):
    db = tmp_path / "governance.sqlite3"
    with pytest.raises(ValueError, match="scope"):
        create_waiver(db, rule_id="r", scope={}, reason="Valid reason here",
                      created_by="alice", expires_at=time.time() + 60)
    with pytest.raises(ValueError, match="future"):
        create_waiver(db, rule_id="r", scope={"project": "x"}, reason="Valid reason here",
                      created_by="alice", expires_at=time.time() - 1)
    waiver = create_waiver(db, rule_id="r", scope={"project": "x"},
                           reason="Valid reason here", created_by="alice",
                           expires_at=time.time() + 3600)
    assert not waiver_applies(waiver, rule_id="r", context={"project": "x"},
                              now=waiver["expires_at"] + 1)
    with pytest.raises(ValueError, match="at least 8"):
        create_waiver(db, rule_id="r", scope={"project": "x"}, reason="no",
                      created_by="alice", expires_at=time.time() + 60)
