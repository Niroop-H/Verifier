"""Golden corpus integrity and mutation benchmark accounting."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA = "mqv-aegis-quality/1.0"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def evaluate_mutation_results(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate mutation score from explicit observed outcomes; do not execute RTL here."""
    if not isinstance(records, list) or not records:
        raise ValueError("Mutation results must be a non-empty list")
    ids = [record.get("id") for record in records if isinstance(record, dict)]
    if len(ids) != len(records) or any(not isinstance(item, str) or not item for item in ids):
        raise ValueError("Every mutation record must be an object with a non-empty id")
    if len(set(ids)) != len(ids):
        raise ValueError("Mutation IDs must be unique")
    rows = []
    for item in records:
        expected = item.get("expected_detection")
        observed = str(item.get("observed_status", "UNKNOWN")).upper()
        if not isinstance(expected, bool):
            raise ValueError(f"Mutation {item['id']} requires boolean expected_detection")
        detected = observed in {"FAIL", "ERROR", "BLOCKED"}
        equivalent = bool(item.get("equivalent", False))
        rows.append({"id": item["id"], "expected_detection": expected, "observed_status": observed,
                     "detected": detected, "equivalent": equivalent,
                     "result": "KILLED" if detected and expected else (
                         "SURVIVED" if expected and not detected else (
                             "FALSE_ALARM" if not expected and detected else "NOT_EXPECTED_TO_DETECT"))})
    eligible = [row for row in rows if row["expected_detection"] and not row["equivalent"]]
    killed = sum(row["detected"] for row in eligible)
    return {
        "schema": SCHEMA, "analysis": "mutation-benchmark-accounting", "mutant_count": len(rows),
        "eligible_mutant_count": len(eligible), "killed_count": killed,
        "survived_count": sum(row["result"] == "SURVIVED" for row in rows),
        "false_alarm_count": sum(row["result"] == "FALSE_ALARM" for row in rows),
        "mutation_score": round(killed / len(eligible), 6) if eligible else None,
        "records": rows,
        "methodology": "Mutation score = detected eligible mutants / eligible non-equivalent mutants.",
        "limitations": ["This computes metrics from supplied outcomes; it does not itself mutate or simulate RTL.",
                        "Results are meaningful only when mutant corpus and detection criteria are reviewed and versioned.",
                        "A high mutation score does not prove absence of design defects."],
    }


def validate_golden_corpus(root: Path, manifest_path: Path) -> dict[str, Any]:
    """Validate fixture membership, hashes, and explicit expected outcomes in a corpus manifest."""
    root = Path(root).resolve()
    try:
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read golden corpus manifest: {exc}") from exc
    if not isinstance(manifest, dict) or not isinstance(manifest.get("fixtures"), list):
        raise ValueError("Golden corpus manifest must contain a fixtures array")
    issues, rows, seen = [], [], set()
    for fixture in manifest["fixtures"]:
        if not isinstance(fixture, dict):
            issues.append("Fixture entry is not an object")
            continue
        path_text = fixture.get("path")
        expected = fixture.get("expected_outcome")
        digest = fixture.get("sha256")
        if not isinstance(path_text, str) or not path_text or Path(path_text).is_absolute() or ".." in Path(path_text).parts:
            issues.append(f"Unsafe fixture path: {path_text!r}")
            continue
        if path_text in seen:
            issues.append(f"Duplicate fixture path: {path_text}")
            continue
        seen.add(path_text)
        if not isinstance(expected, str) or not expected.strip():
            issues.append(f"{path_text}: expected_outcome is missing")
        path = (root / path_text).resolve()
        if not path.is_relative_to(root):
            issues.append(f"{path_text}: path escapes corpus root")
            continue
        if path.is_symlink() or not path.is_file():
            issues.append(f"{path_text}: fixture file missing or is symlink")
            rows.append({"path": path_text, "status": "MISSING_OR_INVALID"})
            continue
        actual = _sha256(path)
        valid_hash = isinstance(digest, str) and actual == digest
        if not valid_hash:
            issues.append(f"{path_text}: SHA-256 missing or mismatched")
        rows.append({"path": path_text, "status": "VALID" if valid_hash and expected else "INVALID",
                     "sha256": actual, "expected_outcome": expected})
    return {
        "schema": SCHEMA, "manifest_version": manifest.get("version"),
        "fixture_count": len(rows), "valid_count": sum(row["status"] == "VALID" for row in rows),
        "status": "PASS" if rows and not issues else "INVALID",
        "issues": issues, "fixtures": rows,
        "limitations": ["A valid hash proves fixture bytes match the manifest, not that expected outcomes are correct.",
                        "Expected-outcome changes require human review and a rationale in version control."],
    }
