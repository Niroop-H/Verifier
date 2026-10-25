"""Evidence-gated readiness assessment for MQV.

This is a policy evaluator, not a physical sign-off engine. It never upgrades a
missing or unexecuted verification result to PASS and only evaluates a declared
scope and caller-supplied evidence inventory.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from .models import Status
from .verification_catalog import get_verification_unit


class Readiness(str, Enum):
    INCOMPLETE = "INCOMPLETE"
    BLOCKED = "BLOCKED"
    NOT_READY = "NOT READY"
    REVIEW_REQUIRED = "REVIEW REQUIRED"
    EVIDENCE_COMPLETE = "EVIDENCE COMPLETE — SIGN-OFF STILL REQUIRED"


@dataclass(frozen=True)
class EvidenceRecord:
    unit_id: str
    status: Status
    evidence_uri: str | None = None
    input_digest: str | None = None
    tool_version: str | None = None
    reviewed_by: str | None = None


@dataclass(frozen=True)
class ReadinessAssessment:
    readiness: Readiness
    scope: str
    passed: tuple[str, ...]
    failed: tuple[str, ...]
    blocked: tuple[str, ...]
    missing: tuple[str, ...]
    unreviewed: tuple[str, ...]
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "readiness": self.readiness.value,
            "scope": self.scope,
            "passed": list(self.passed),
            "failed": list(self.failed),
            "blocked": list(self.blocked),
            "missing": list(self.missing),
            "unreviewed": list(self.unreviewed),
            "notes": list(self.notes),
            "fabrication_ready": False,
        }


def assess_readiness(
    *,
    scope: str,
    required_units: Iterable[str],
    evidence: Iterable[EvidenceRecord],
    require_human_review: bool = True,
) -> ReadinessAssessment:
    """Assess only supplied evidence; never emit a fabrication-ready verdict.

    Duplicate evidence for a required unit is ambiguous and treated as missing.
    A PASS requires an evidence URI and input digest. Human review is independently
    required by default. This policy does not authenticate evidence contents.
    """
    scope = scope.strip()
    if not scope:
        raise ValueError("A non-empty assessment scope is required.")
    required = tuple(dict.fromkeys(required_units))
    if not required:
        raise ValueError("At least one required verification unit must be declared.")
    unknown = [unit_id for unit_id in required if get_verification_unit(unit_id) is None]
    if unknown:
        raise ValueError("Unknown verification unit(s): " + ", ".join(unknown))

    records: dict[str, list[EvidenceRecord]] = {}
    for item in evidence:
        if item.unit_id in required:
            records.setdefault(item.unit_id, []).append(item)

    passed: list[str] = []
    failed: list[str] = []
    blocked: list[str] = []
    missing: list[str] = []
    unreviewed: list[str] = []
    for unit_id in required:
        matches = records.get(unit_id, [])
        if len(matches) != 1:
            missing.append(unit_id)
            continue
        record = matches[0]
        if record.status == Status.FAIL:
            failed.append(unit_id)
        elif record.status in (Status.BLOCKED, Status.ERROR, Status.INCONCLUSIVE):
            blocked.append(unit_id)
        elif record.status != Status.PASS:
            missing.append(unit_id)
        elif not record.evidence_uri or not record.input_digest:
            missing.append(unit_id)
        else:
            passed.append(unit_id)
            if require_human_review and not record.reviewed_by:
                unreviewed.append(unit_id)

    notes = (
        "Assessment is limited to the declared scope and supplied evidence records.",
        "Evidence contents, input digests, tool versions and reviewer identities are not independently authenticated here.",
        "This policy assessment is not foundry sign-off and never declares fabrication readiness.",
    )
    if failed:
        readiness = Readiness.NOT_READY
    elif blocked:
        readiness = Readiness.BLOCKED
    elif missing:
        readiness = Readiness.INCOMPLETE
    elif unreviewed:
        readiness = Readiness.REVIEW_REQUIRED
    else:
        readiness = Readiness.EVIDENCE_COMPLETE
    return ReadinessAssessment(readiness, scope, tuple(passed), tuple(failed), tuple(blocked),
                               tuple(missing), tuple(unreviewed), notes)
