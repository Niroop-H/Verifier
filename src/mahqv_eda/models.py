"""Typed, auditable outcomes for EDA runs."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

class Status(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    INCONCLUSIVE = "INCONCLUSIVE"
    NOT_RUN = "NOT RUN"
    ERROR = "ERROR"

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass
class EdaResult:
    check: str
    status: Status
    message: str
    command: list[str]
    return_code: int | None = None
    started_at: str | None = None
    duration_seconds: float = 0.0
    stdout: str = ""
    stderr: str = ""
    tool_version: str | None = None
    evidence: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data
