import pytest

from mqv_eda.job_queue import enqueue, claim_next, cancel_job, transition, get_job, list_jobs, job_health, finish_job


def test_queue_lifecycle_persists_events_and_terminal_state(tmp_path):
    db = tmp_path / "jobs.sqlite3"
    job = enqueue(db, {"source": "fixtures/demo"}, actor="tester")
    assert job["state"] == "QUEUED"
    claimed = claim_next(db, worker_id="worker-1")
    assert claimed["id"] == job["id"]
    assert claimed["state"] == "RUNNING"
    done = transition(db, job["id"], "SUCCEEDED", actor="worker-1", detail="report saved")
    assert done["state"] == "SUCCEEDED"
    assert [e["to_state"] for e in done["events"]] == ["QUEUED", "RUNNING", "SUCCEEDED"]
    assert get_job(db, job["id"])["payload"] == {"source": "fixtures/demo"}
    assert job_health(db)["counts"]["SUCCEEDED"] == 1


def test_cancel_queued_job_and_reject_illegal_transition(tmp_path):
    db = tmp_path / "jobs.sqlite3"
    job = enqueue(db, {})
    cancelled = cancel_job(db, job["id"])
    assert cancelled["state"] == "CANCELLED"
    assert claim_next(db, worker_id="worker") is None
    with pytest.raises(ValueError, match="terminal state"):
        cancel_job(db, job["id"])


def test_running_cancel_is_cooperative_and_worker_acknowledges(tmp_path):
    db = tmp_path / "jobs.sqlite3"
    job = enqueue(db, {})
    claim_next(db, worker_id="worker")
    requested = cancel_job(db, job["id"])
    assert requested["state"] == "CANCEL_REQUESTED"
    assert requested["cancel_requested"] is True
    final = transition(db, job["id"], "CANCELLED", actor="worker", detail="process terminated")
    assert final["state"] == "CANCELLED"


def test_invalid_transition_and_unknown_id_are_rejected(tmp_path):
    db = tmp_path / "jobs.sqlite3"
    job = enqueue(db, {})
    with pytest.raises(ValueError, match="invalid job transition"):
        transition(db, job["id"], "SUCCEEDED", actor="cli")
    with pytest.raises(ValueError, match="unknown job id"):
        get_job(db, "missing")
    with pytest.raises(ValueError, match="between 1 and 1000"):
        list_jobs(db, limit=0)



def test_only_claiming_worker_can_finish_job(tmp_path):
    db = tmp_path / "jobs.sqlite3"
    job = enqueue(db, {"source": "fixture"})
    claim_next(db, worker_id="worker-a")
    with pytest.raises(ValueError, match="does not own"):
        finish_job(db, job["id"], worker_id="worker-b", state="SUCCEEDED")
    finished = finish_job(db, job["id"], worker_id="worker-a",
                          state="SUCCEEDED", detail="report persisted")
    assert finished["state"] == "SUCCEEDED"
    assert finished["events"][-1]["actor"] == "worker-a"
