from __future__ import annotations
from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Any
from datetime import datetime, timezone

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

class Status(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    INCONCLUSIVE = "INCONCLUSIVE"
    NOT_RUN = "NOT RUN"
    ERROR = "ERROR"

@dataclass
class CheckResult:
    stage: str
    status: Status
    message: str
    required: bool = True
    command: list[str] = field(default_factory=list)
    tool_version: str | None = None
    started_utc: str = field(default_factory=utc_now)
    duration_seconds: float = 0.0
    exit_code: int | None = None
    input_hashes: dict[str, str] = field(default_factory=dict)
    log_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        return value

def aggregate_status(results: list[CheckResult]) -> Status:
    required = [r for r in results if r.required]
    if not required:
        return Status.NOT_RUN
    statuses = {r.status for r in required}
    # Fail closed. Tool or infrastructure failures must never become PASS.
    for state in (Status.ERROR, Status.FAIL, Status.BLOCKED, Status.INCONCLUSIVE, Status.NOT_RUN):
        if state in statuses:
            return state
    return Status.PASS if statuses == {Status.PASS} else Status.ERROR
