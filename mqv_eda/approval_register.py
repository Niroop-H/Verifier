"""Durable local approval decision register.

Local SQLite persistence only; actor labels are not authenticated identities.
"""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any


def _connect(database: Path) -> sqlite3.Connection:
    database = Path(database)
    database.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(database), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("""CREATE TABLE IF NOT EXISTS approvals (
        id TEXT PRIMARY KEY, run_id TEXT NOT NULL, report_sha256 TEXT NOT NULL,
        actor TEXT NOT NULL, role TEXT NOT NULL, decision TEXT NOT NULL,
        rationale TEXT NOT NULL, run_operator TEXT, policy_author TEXT,
        require_separation INTEGER NOT NULL, created_at REAL NOT NULL
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS approval_events (
        seq INTEGER PRIMARY KEY AUTOINCREMENT, approval_id TEXT NOT NULL,
        at REAL NOT NULL, action TEXT NOT NULL, actor TEXT NOT NULL, detail TEXT NOT NULL,
        FOREIGN KEY(approval_id) REFERENCES approvals(id)
    )""")
    return conn


def _render(conn: sqlite3.Connection, approval_id: str) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM approvals WHERE id=?", (approval_id,)).fetchone()
    if row is None:
        raise ValueError(f"unknown approval id: {approval_id}")
    result = dict(row)
    result["require_separation"] = bool(result["require_separation"])
    result["events"] = [dict(event) for event in conn.execute(
        "SELECT at,action,actor,detail FROM approval_events WHERE approval_id=? ORDER BY seq",
        (approval_id,),
    )]
    return result


def create_approval(database: Path, *, run_id: str, report_sha256: str, actor: str,
                    role: str, decision: str, rationale: str,
                    run_operator: str | None = None, policy_author: str | None = None,
                    require_separation: bool = True) -> dict[str, Any]:
    required = {"run_id": run_id, "report_sha256": report_sha256,
                "actor": actor, "role": role, "rationale": rationale}
    if any(not isinstance(value, str) or not value.strip() for value in required.values()):
        raise ValueError("run_id, report_sha256, actor, role, and rationale are required")
    if len(report_sha256) != 64 or any(ch not in "0123456789abcdefABCDEF" for ch in report_sha256):
        raise ValueError("report_sha256 must be a 64-character hexadecimal SHA-256")
    if decision not in {"APPROVE", "REJECT"}:
        raise ValueError("decision must be APPROVE or REJECT")
    blockers = []
    if decision == "APPROVE" and require_separation:
        if actor.strip() == (run_operator or "").strip():
            blockers.append("Approver must differ from the run operator")
        if actor.strip() == (policy_author or "").strip():
            blockers.append("Approver must differ from the policy author")
    status = "BLOCKED" if blockers else ("APPROVED" if decision == "APPROVE" else "REJECTED")
    approval_id = str(uuid.uuid4())
    now = time.time()
    with _connect(database) as conn:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("""INSERT INTO approvals
            (id,run_id,report_sha256,actor,role,decision,rationale,run_operator,policy_author,
             require_separation,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (approval_id, run_id.strip(), report_sha256.lower(), actor.strip(), role.strip(),
             decision, rationale.strip(), run_operator, policy_author, int(require_separation), now))
        detail = json.dumps({"status": status, "blockers": blockers}, sort_keys=True)
        conn.execute("INSERT INTO approval_events(approval_id,at,action,actor,detail) VALUES(?,?,?,?,?)",
                     (approval_id, now, "DECISION_RECORDED", actor.strip(), detail))
    result = get_approval(database, approval_id)
    result["status"] = status
    result["blockers"] = blockers
    return result


def get_approval(database: Path, approval_id: str) -> dict[str, Any]:
    with _connect(database) as conn:
        return _render(conn, approval_id)


def list_approvals(database: Path, *, limit: int = 100) -> list[dict[str, Any]]:
    if limit < 1 or limit > 1000:
        raise ValueError("limit must be between 1 and 1000")
    with _connect(database) as conn:
        rows = conn.execute("SELECT id FROM approvals ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        results = [_render(conn, row["id"]) for row in rows]
    for result in results:
        events = result.get("events", [])
        if events:
            try:
                result["status"] = json.loads(events[-1]["detail"]).get("status", result["decision"])
            except (ValueError, TypeError):
                result["status"] = result["decision"]
    return results
