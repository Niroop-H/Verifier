"""Durable local waiver register for verification-policy exceptions.

This SQLite implementation provides persistence and an append-only event trail on
one trusted filesystem. It does not authenticate actors or replace server-side
authorization, protected storage, or multi-user concurrency controls.
"""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

STATUSES = {"ACTIVE", "REVOKED", "EXPIRED"}


def _connect(database: Path) -> sqlite3.Connection:
    database = Path(database)
    database.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(database), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("""CREATE TABLE IF NOT EXISTS waivers (
        id TEXT PRIMARY KEY, rule_id TEXT NOT NULL, scope_json TEXT NOT NULL,
        reason TEXT NOT NULL, created_by TEXT NOT NULL, created_at REAL NOT NULL,
        expires_at REAL NOT NULL, status TEXT NOT NULL, revoked_by TEXT,
        revoked_at REAL, version INTEGER NOT NULL DEFAULT 1
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS waiver_events (
        seq INTEGER PRIMARY KEY AUTOINCREMENT, waiver_id TEXT NOT NULL,
        at REAL NOT NULL, action TEXT NOT NULL, actor TEXT NOT NULL,
        detail TEXT NOT NULL,
        FOREIGN KEY(waiver_id) REFERENCES waivers(id)
    )""")
    return conn


def _record_event(conn: sqlite3.Connection, waiver_id: str, action: str,
                  actor: str, detail: str) -> None:
    conn.execute("INSERT INTO waiver_events(waiver_id,at,action,actor,detail) VALUES(?,?,?,?,?)",
                 (waiver_id, time.time(), action, actor, detail))


def _render(conn: sqlite3.Connection, waiver_id: str) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM waivers WHERE id=?", (waiver_id,)).fetchone()
    if row is None:
        raise ValueError(f"unknown waiver id: {waiver_id}")
    result = dict(row)
    result["scope"] = json.loads(result.pop("scope_json"))
    result["events"] = [dict(e) for e in conn.execute(
        "SELECT at,action,actor,detail FROM waiver_events WHERE waiver_id=? ORDER BY seq",
        (waiver_id,)).fetchall()]
    if result["status"] == "ACTIVE" and result["expires_at"] <= time.time():
        result["status"] = "EXPIRED"
    return result


def create_waiver(database: Path, *, rule_id: str, scope: dict[str, Any],
                  reason: str, created_by: str, expires_at: float) -> dict[str, Any]:
    """Create a scoped, expiring exception; expiry is a Unix timestamp."""
    if not isinstance(rule_id, str) or not rule_id.strip():
        raise ValueError("rule_id must be non-empty")
    if not isinstance(scope, dict) or not scope:
        raise ValueError("scope must be a non-empty JSON object")
    if not isinstance(reason, str) or len(reason.strip()) < 8:
        raise ValueError("reason must contain at least 8 non-whitespace characters")
    if not isinstance(created_by, str) or not created_by.strip():
        raise ValueError("created_by must be non-empty")
    if not isinstance(expires_at, (int, float)) or isinstance(expires_at, bool) or expires_at <= time.time():
        raise ValueError("expires_at must be a future Unix timestamp")
    try:
        scope_json = json.dumps(scope, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("scope must be JSON-serializable without NaN or Infinity") from exc
    waiver_id, now = str(uuid.uuid4()), time.time()
    with _connect(database) as conn:
        conn.execute("""INSERT INTO waivers(id,rule_id,scope_json,reason,created_by,created_at,expires_at,status)
                        VALUES(?,?,?,?,?,?,?,'ACTIVE')""",
                     (waiver_id, rule_id.strip(), scope_json, reason.strip(), created_by.strip(), now, float(expires_at)))
        _record_event(conn, waiver_id, "CREATED", created_by.strip(), "scoped waiver created")
        return _render(conn, waiver_id)


def get_waiver(database: Path, waiver_id: str) -> dict[str, Any]:
    with _connect(database) as conn:
        return _render(conn, waiver_id)


def list_waivers(database: Path, *, include_expired: bool = True) -> list[dict[str, Any]]:
    with _connect(database) as conn:
        ids = [r["id"] for r in conn.execute("SELECT id FROM waivers ORDER BY created_at DESC").fetchall()]
        items = [_render(conn, waiver_id) for waiver_id in ids]
    if not include_expired:
        items = [item for item in items if item["status"] == "ACTIVE" and item["expires_at"] > time.time()]
    return items


def revoke_waiver(database: Path, waiver_id: str, *, actor: str, reason: str) -> dict[str, Any]:
    if not isinstance(actor, str) or not actor.strip():
        raise ValueError("actor must be non-empty")
    if not isinstance(reason, str) or len(reason.strip()) < 4:
        raise ValueError("revocation reason must contain at least 4 non-whitespace characters")
    with _connect(database) as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT status,expires_at FROM waivers WHERE id=?", (waiver_id,)).fetchone()
        if row is None:
            raise ValueError(f"unknown waiver id: {waiver_id}")
        if row["status"] != "ACTIVE" or row["expires_at"] <= time.time():
            raise ValueError("only an unexpired active waiver can be revoked")
        now = time.time()
        conn.execute("""UPDATE waivers SET status='REVOKED',revoked_by=?,revoked_at=?,version=version+1
                        WHERE id=? AND status='ACTIVE'""", (actor.strip(), now, waiver_id))
        _record_event(conn, waiver_id, "REVOKED", actor.strip(), reason.strip())
        return _render(conn, waiver_id)


def waiver_applies(waiver: dict[str, Any], *, rule_id: str,
                   context: dict[str, Any], now: float | None = None) -> bool:
    """Exact-match scope check. This deliberately avoids wildcard interpretation."""
    current = time.time() if now is None else now
    if waiver.get("status") != "ACTIVE" or float(waiver.get("expires_at", 0)) <= current:
        return False
    if waiver.get("rule_id") != rule_id:
        return False
    scope = waiver.get("scope")
    if not isinstance(scope, dict) or not scope:
        return False
    return all(key in context and context[key] == value for key, value in scope.items())
