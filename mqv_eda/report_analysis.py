"""Deterministic report comparison and evidence-backed failure triage.

These helpers analyze existing Aegis/MQV JSON reports and logs. They do not
reinterpret a tool's PASS as chip sign-off and do not generate ungrounded claims.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

SCHEMA = "1.0"
_SOURCE_LOC = re.compile(r"(?P<path>(?:[A-Za-z]:)?[^\s:()]+\.(?:sv|v|vhd|vhdl|vh|svh)):(?P<line>\d+)(?::(?P<column>\d+))?")
_ERROR_PATTERNS = [
    ("syntax", re.compile(r"syntax error|parse error|unexpected token|syntax error near", re.I),
     "Inspect the reported source location and parser context; check delimiters, declarations, and language mode."),
    ("elaboration", re.compile(r"unknown module|module .* not found|cannot find .*module|undefined module", re.I),
     "Check source-file inclusion, module names, library search paths, and the selected top."),
    ("assertion", re.compile(r"assertion failed|assertion.*fail|\$fatal|\$error", re.I),
     "Inspect the failing assertion and test inputs. Treat this as a real design/test failure until explained."),
    ("timeout", re.compile(r"timed out|timeout|time limit", re.I),
     "Inspect the last log activity and design/testbench progress; distinguish a genuine hang from a too-small timeout."),
    ("timing", re.compile(r"slack.*violated|negative slack|setup violation|hold violation", re.I),
     "Review the exact SDC, Liberty, clock definitions, path report, and analysis assumptions."),
    ("missing-input", re.compile(r"no such file|cannot open|failed to open|file not found", re.I),
     "Verify the input path, permissions, working directory, and whether the required file is included in the evidence bundle."),
]

def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read JSON report {path}: {exc}") from exc
    if not isinstance(value, dict) or not isinstance(value.get("checks"), list):
        raise ValueError(f"{path} is not a supported Aegis/MQV report (missing checks array)")
    return value

def _check_map(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for check in report["checks"]:
        if not isinstance(check, dict) or not isinstance(check.get("stage"), str):
            continue
        stage = check["stage"]
        # Duplicate stage names are ambiguous; keep them explicit rather than silently overwrite.
        key = stage
        index = 2
        while key in result:
            key = f"{stage}#{index}"
            index += 1
        result[key] = check
    return result

def compare_reports(baseline_path: Path, candidate_path: Path) -> dict[str, Any]:
    """Compare two reports conservatively; missing stages are never treated as passes."""
    baseline = _load(baseline_path)
    candidate = _load(candidate_path)
    left, right = _check_map(baseline), _check_map(candidate)
    rows = []
    for stage in sorted(set(left) | set(right)):
        old, new = left.get(stage), right.get(stage)
        if old is None:
            change = "ADDED"
        elif new is None:
            change = "REMOVED"
        elif old.get("status") != new.get("status"):
            change = "STATUS_CHANGED"
        elif old.get("input_hashes", {}) != new.get("input_hashes", {}):
            change = "INPUTS_CHANGED"
        elif old.get("tool_version") != new.get("tool_version"):
            change = "TOOL_VERSION_CHANGED"
        elif old.get("duration_seconds") != new.get("duration_seconds"):
            change = "DURATION_CHANGED"
        else:
            change = "UNCHANGED"
        rows.append({
            "stage": stage,
            "change": change,
            "baseline_status": old.get("status") if old else None,
            "candidate_status": new.get("status") if new else None,
            "baseline_duration_seconds": old.get("duration_seconds") if old else None,
            "candidate_duration_seconds": new.get("duration_seconds") if new else None,
            "baseline_input_hashes": old.get("input_hashes", {}) if old else None,
            "candidate_input_hashes": new.get("input_hashes", {}) if new else None,
            "baseline_tool_version": old.get("tool_version") if old else None,
            "candidate_tool_version": new.get("tool_version") if new else None,
            "candidate_message": new.get("message") if new else None,
        })
    regressions = [r for r in rows if
        (r["baseline_status"] == "PASS" and r["candidate_status"] not in (None, "PASS"))
        or r["change"] == "REMOVED"]
    return {
        "schema_version": SCHEMA,
        "analysis": "report-comparison",
        "baseline_report_sha256": hashlib.sha256(Path(baseline_path).read_bytes()).hexdigest(),
        "candidate_report_sha256": hashlib.sha256(Path(candidate_path).read_bytes()).hexdigest(),
        "baseline_overall_status": baseline.get("overall_status"),
        "candidate_overall_status": candidate.get("overall_status"),
        "regression_count": len(regressions),
        "regressions": regressions,
        "changes": rows,
        "limitations": [
            "This compares recorded report fields only; it does not independently validate tool results.",
            "A removed check is treated as a review-required regression because evidence disappeared.",
            "Different configurations or tool versions may make direct comparisons non-equivalent.",
            "A PASS applies only to the configured check, not to chip fabrication readiness.",
        ],
    }

def triage_log(log_path: Path) -> dict[str, Any]:
    """Produce deterministic, evidence-linked triage suggestions from a text log."""
    path = Path(log_path)
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise ValueError(f"Cannot read log {path}: {exc}") from exc
    lines = content.splitlines()
    findings = []
    seen = set()
    for number, line in enumerate(lines, start=1):
        for kind, pattern, advice in _ERROR_PATTERNS:
            if not pattern.search(line):
                continue
            key = (kind, number)
            if key in seen:
                continue
            seen.add(key)
            location = None
            match = _SOURCE_LOC.search(line)
            if match:
                location = {
                    "path": match.group("path"),
                    "line": int(match.group("line")),
                    "column": int(match.group("column")) if match.group("column") else None,
                }
            findings.append({
                "category": kind,
                "log_line": number,
                "evidence": line[:1000],
                "source_location": location,
                "suggestion": advice,
                "confidence": "pattern_match_requires_engineer_review",
            })
    if not findings:
        findings.append({
            "category": "no-recognized-pattern",
            "log_line": None,
            "evidence": None,
            "source_location": None,
            "suggestion": "No known failure signature matched. Review the raw log and tool-specific report manually.",
            "confidence": "no_inference",
        })
    return {
        "schema_version": SCHEMA,
        "analysis": "log-triage",
        "log_name": path.name,
        "log_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "line_count": len(lines),
        "finding_count": len(findings),
        "findings": findings,
        "limitations": [
            "Suggestions are deterministic heuristics, not root-cause proof.",
            "Source locations are extracted only when present in the matching log line.",
            "Always inspect the original tool output and verify suggestions before changing RTL.",
        ],
    }

def write_json(value: dict[str, Any], output: Path) -> Path:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output
