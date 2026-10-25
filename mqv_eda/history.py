"""Regression history and failure-cover minimization."""
from __future__ import annotations
import json
from pathlib import Path

SCHEMA = "mqv-aegis-history/1.0"


def regression_history(report_paths: list[Path]) -> dict:
    if not report_paths:
        raise ValueError("At least one report is required")
    runs = []
    for path in report_paths:
        try:
            report = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Cannot read report {path}: {exc}") from exc
        if not isinstance(report, dict) or not isinstance(report.get("checks"), list):
            raise ValueError(f"Unsupported report {path}: expected checks array")
        counts = {key: 0 for key in ("PASS", "FAIL", "BLOCKED", "INCONCLUSIVE", "NOT RUN", "ERROR", "UNKNOWN")}
        duration = 0.0
        for check in report["checks"]:
            if not isinstance(check, dict):
                counts["UNKNOWN"] += 1
                continue
            status = str(check.get("status", "UNKNOWN")).upper()
            counts[status if status in counts else "UNKNOWN"] += 1
            try:
                duration += max(0.0, float(check.get("duration_seconds", 0)))
            except (TypeError, ValueError):
                counts["UNKNOWN"] += 1
        runs.append({"report": Path(path).name, "run_id": report.get("run_id"),
                     "created_utc": report.get("created_utc") or report.get("timestamp"),
                     "overall_status": report.get("overall_status", report.get("status", "UNKNOWN")),
                     "check_counts": counts, "duration_seconds": round(duration, 3)})
    return {"schema": SCHEMA, "report_count": len(runs), "runs": runs, "latest_run": runs[-1],
            "limitations": ["Input order is preserved; reports are not sorted by timestamp.",
                            "Missing duration is not a measured zero runtime.",
                            "Preserve failed and cancelled runs to avoid survivorship bias."]}


def minimize_failure_cover(cases: list[dict]) -> dict:
    """Greedy test-subset suggestion from supplied failure mappings; does not execute tests."""
    if not isinstance(cases, list) or not cases:
        raise ValueError("cases must be a non-empty list")
    normalized, seen = [], set()
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("test_id"), str) or not case["test_id"]:
            raise ValueError("Each case requires a non-empty test_id")
        if case["test_id"] in seen:
            raise ValueError(f"Duplicate test_id: {case['test_id']}")
        seen.add(case["test_id"])
        failures = case.get("failure_ids")
        if not isinstance(failures, list) or any(not isinstance(x, str) or not x for x in failures):
            raise ValueError(f"{case['test_id']} failure_ids must be a list of non-empty strings")
        normalized.append({"test_id": case["test_id"], "failure_ids": set(failures)})
    remaining = set().union(*(case["failure_ids"] for case in normalized))
    original_count, selected = len(remaining), []
    while remaining:
        candidates = sorted(normalized, key=lambda item: (-len(item["failure_ids"] & remaining), item["test_id"]))
        gain = candidates[0]["failure_ids"] & remaining
        if not gain:
            break
        selected.append({"test_id": candidates[0]["test_id"], "covers_failure_ids": sorted(gain)})
        remaining -= gain
    return {"schema": SCHEMA, "algorithm": "greedy-set-cover", "input_case_count": len(normalized),
            "selected_case_count": len(selected), "original_failure_id_count": original_count,
            "covered_failure_id_count": original_count - len(remaining), "uncovered_failure_ids": sorted(remaining),
            "selected_cases": selected,
            "limitations": ["Heuristic subset suggestion only; it does not rerun tests or prove reproduction.",
                            "Keep original tests and artifacts; validate the subset in the real runner.",
                            "Greedy set cover is not guaranteed globally minimal."]}
