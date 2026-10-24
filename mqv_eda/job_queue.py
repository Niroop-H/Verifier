"""SQLite-backed job lifecycle primitives for local and single-host deployments.

This is durable on one filesystem, not a distributed queue. Worker execution and
multi-host leasing belong to a future control-plane deployment.
"""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

TERMINAL = {"SUCCEEDED", "FAILED", "CANCELLED"}
TRANSITIONS = {
    "QUEUED": {"RUNNING", "CANCELLED"},
    "RUNNING": {"SUCCEEDED", "FAILED", "CANCEL_REQUESTED"},
    "CANCEL_REQUESTED": {"CANCELLED", "FAILED"},
    "SUCCEEDED": set(), "FAILED": set(), "CANCELLED": set(),
}


def _connect(database: Path) -> sqlite3.Connection:
    database = Path(database)
    database.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(database), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY, payload_json TEXT NOT NULL, state TEXT NOT NULL,
        created_at REAL NOT NULL, updated_at REAL NOT NULL, started_at REAL,
        finished_at REAL, worker_id TEXT, cancel_requested INTEGER NOT NULL DEFAULT 0,
        error TEXT, version INTEGER NOT NULL DEFAULT 1
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS job_events (
        seq INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT NOT NULL,
        at REAL NOT NULL, from_state TEXT, to_state TEXT NOT NULL,
        actor TEXT NOT NULL, detail TEXT NOT NULL,
        FOREIGN KEY(job_id) REFERENCES jobs(id)
    )""")
    return conn


def _event(conn: sqlite3.Connection, job_id: str, before: str | None,
           after: str, actor: str, detail: str) -> None:
    conn.execute("INSERT INTO job_events(job_id,at,from_state,to_state,actor,detail) VALUES(?,?,?,?,?,?)",
                 (job_id, time.time(), before, after, actor, detail))


def enqueue(database: Path, payload: dict[str, Any], *, actor: str = "cli") -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("job payload must be a JSON object")
    now, job_id = time.time(), str(uuid.uuid4())
    with _connect(database) as conn:
        conn.execute("INSERT INTO jobs(id,payload_json,state,created_at,updated_at) VALUES(?,?,?,?,?)",
                     (job_id, json.dumps(payload, sort_keys=True), "QUEUED", now, now))
        _event(conn, job_id, None, "QUEUED", actor, "job accepted")
    return get_job(database, job_id)


def get_job(database: Path, job_id: str) -> dict[str, Any]:
    with _connect(database) as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if row is None:
            raise ValueError(f"unknown job id: {job_id}")
        events = conn.execute("SELECT at,from_state,to_state,actor,detail FROM job_events WHERE job_id=? ORDER BY seq",
                              (job_id,)).fetchall()
    result = dict(row)
    result["payload"] = json.loads(result.pop("payload_json"))
    result["cancel_requested"] = bool(result["cancel_requested"])
    result["events"] = [dict(e) for e in events]
    return result


def list_jobs(database: Path, *, limit: int = 100) -> list[dict[str, Any]]:
    if not 1 <= limit <= 1000:
        raise ValueError("limit must be between 1 and 1000")
    with _connect(database) as conn:
        ids = [r["id"] for r in conn.execute(
            "SELECT id FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()]
    return [get_job(database, job_id) for job_id in ids]


def claim_next(database: Path, *, worker_id: str) -> dict[str, Any] | None:
    if not worker_id or not worker_id.strip():
        raise ValueError("worker_id must be non-empty")
    with _connect(database) as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT id,state FROM jobs WHERE state='QUEUED' ORDER BY created_at,id LIMIT 1").fetchone()
        if row is None:
            return None
        now = time.time()
        changed = conn.execute("""UPDATE jobs SET state='RUNNING',worker_id=?,started_at=?,updated_at=?,version=version+1
                                  WHERE id=? AND state='QUEUED'""",
                               (worker_id, now, now, row["id"])).rowcount
        if changed != 1:
            return None
        _event(conn, row["id"], "QUEUED", "RUNNING", worker_id, "worker claimed job")
    return get_job(database, row["id"])


def transition(database: Path, job_id: str, new_state: str, *, actor: str,
               detail: str = "", error: str | None = None) -> dict[str, Any]:
    if new_state not in TRANSITIONS:
        raise ValueError(f"unsupported job state: {new_state}")
    with _connect(database) as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT state FROM jobs WHERE id=?", (job_id,)).fetchone()
        if row is None:
            raise ValueError(f"unknown job id: {job_id}")
        old = row["state"]
        if new_state not in TRANSITIONS[old]:
            raise ValueError(f"invalid job transition: {old} -> {new_state}")
        now = time.time()
        conn.execute("""UPDATE jobs SET state=?,updated_at=?,finished_at=?,error=?,cancel_requested=?,
                        version=version+1 WHERE id=?""",
                     (new_state, now, now if new_state in TERMINAL else None, error,
                      1 if new_state == "CANCEL_REQUESTED" else 0, job_id))
        _event(conn, job_id, old, new_state, actor, detail or "state transition")
    return get_job(database, job_id)


def cancel_job(database: Path, job_id: str, *, actor: str = "cli") -> dict[str, Any]:
    job = get_job(database, job_id)
    if job["state"] == "QUEUED":
        return transition(database, job_id, "CANCELLED", actor=actor, detail="cancelled before execution")
    if job["state"] == "RUNNING":
        return transition(database, job_id, "CANCEL_REQUESTED", actor=actor,
                          detail="cooperative cancellation requested")
    if job["state"] == "CANCEL_REQUESTED":
        return job
    raise ValueError(f"cannot cancel job in terminal state {job['state']}")


def job_health(database: Path) -> dict[str, Any]:
    with _connect(database) as conn:
        counts = {row["state"]: row["n"] for row in conn.execute(
            "SELECT state,COUNT(*) AS n FROM jobs GROUP BY state")}
        total = sum(counts.values())
        return {"queue": "sqlite-local", "durable": True, "distributed": False,
                "total": total, "counts": counts,
                "note": "Running jobs require a worker to poll cancel_requested and acknowledge cancellation."}
