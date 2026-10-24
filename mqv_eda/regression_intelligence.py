"""Transparent regression-quality analytics built from existing evidence.

Heuristics are indicators for engineers, not root-cause proof or a replacement for sign-off.
"""
from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Any

SCHEMA = "mqv-aegis-regression/1.0"
_SECRETISH = re.compile(r"(?i)(token|password|secret|api[_-]?key)\s*[:=]\s*\S+")


def _report(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read report {path}: {exc}") from exc
    if not isinstance(value, dict) or not isinstance(value.get("checks"), list):
        raise ValueError(f"Unsupported report format in {path}: expected checks array")
    return value


def detect_flaky_runs(report_paths: list[Path]) -> dict[str, Any]:
    """Identify stage outcomes that vary across supplied reports; never suppress failures."""
    if len(report_paths) < 2:
        raise ValueError("At least two reports are required to detect outcome variation")
    samples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in report_paths:
        report = _report(path)
        seen: set[str] = set()
        for check in report["checks"]:
            if not isinstance(check, dict) or not isinstance(check.get("stage"), str):
                continue
            stage = check["stage"]
            if stage in seen:
                stage = f"{stage}#duplicate"
            seen.add(stage)
            samples[stage].append({"report": Path(path).name, "status": str(check.get("status", "UNKNOWN")).upper()})
    rows = []
    for stage, outcomes in sorted(samples.items()):
        statuses = sorted({item["status"] for item in outcomes})
        rows.append({
            "stage": stage,
            "sample_count": len(outcomes),
            "observed_statuses": statuses,
            "variable": len(statuses) > 1,
            "outcomes": outcomes,
            "interpretation": "OUTCOME_VARIATION_REQUIRES_INVESTIGATION" if len(statuses) > 1 else "NO_VARIATION_OBSERVED_IN_SAMPLES",
        })
    return {
        "schema": SCHEMA,
        "analysis": "flaky-test-detection",
        "input_report_count": len(report_paths),
        "stages": rows,
        "variable_stage_count": sum(row["variable"] for row in rows),
        "limitations": [
            "A fixed outcome in this sample does not prove a test is non-flaky.",
            "Reports should represent identical inputs and toolchain for a valid flakiness claim.",
            "Failures are reported, never automatically ignored or downgraded.",
        ],
    }


def cluster_failures(log_paths: list[Path]) -> dict[str, Any]:
    """Cluster logs by normalized first failure signature while retaining source references."""
    clusters: dict[str, dict[str, Any]] = {}
    for path in log_paths:
        path = Path(path)
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise ValueError(f"Cannot read log {path}: {exc}") from exc
        lines = text.splitlines()
        candidate = next((line.strip() for line in lines if re.search(
            r"\b(error|fatal|failed|failure|assertion|timeout|timed out)\b", line, re.I)), "")
        normalized = _SECRETISH.sub("[REDACTED]=[VALUE]", candidate)
        normalized = re.sub(r"\b0x[0-9a-f]+\b", "<HEX>", normalized, flags=re.I)
        normalized = re.sub(r"\b\d+\b", "<N>", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip().lower()
        signature = normalized or "NO_RECOGNIZED_FAILURE_LINE"
        key = hashlib.sha256(signature.encode("utf-8")).hexdigest()[:16]
        if key not in clusters:
            clusters[key] = {"cluster_id": key, "signature": signature, "logs": []}
        clusters[key]["logs"].append({"file": path.name, "line": lines.index(candidate) + 1 if candidate else None})
    result = sorted(clusters.values(), key=lambda item: (-len(item["logs"]), item["cluster_id"]))
    return {
        "schema": SCHEMA,
        "analysis": "failure-clustering",
        "log_count": len(log_paths),
        "cluster_count": len(result),
        "clusters": result,
        "limitations": [
            "Clustering uses a deterministic heuristic based on the first matching failure line.",
            "Similar signatures may have different root causes; different signatures may share a cause.",
            "Raw logs should be retained as source evidence; this output is not root-cause proof.",
        ],
    }


def ingest_cobertura_coverage(xml_path: Path) -> dict[str, Any]:
    """Import common Cobertura-style XML line/branch totals without conflating missing with zero."""
    xml_path = Path(xml_path)
    try:
        root = ET.parse(xml_path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise ValueError(f"Cannot parse coverage XML {xml_path}: {exc}") from exc
    def integer_attr(node, key):
        raw = node.attrib.get(key)
        if raw is None:
            return None
        try:
            return int(raw)
        except ValueError:
            return None
    lines_valid = integer_attr(root, "lines-valid")
    lines_covered = integer_attr(root, "lines-covered")
    branches_valid = integer_attr(root, "branches-valid")
    branches_covered = integer_attr(root, "branches-covered")
    def ratio(covered, valid):
        return round(covered / valid, 6) if covered is not None and valid not in (None, 0) else None
    return {
        "schema": SCHEMA,
        "format": "cobertura-xml",
        "source_file": xml_path.name,
        "line_coverage": {"covered": lines_covered, "valid": lines_valid, "ratio": ratio(lines_covered, lines_valid)},
        "branch_coverage": {"covered": branches_covered, "valid": branches_valid, "ratio": ratio(branches_covered, branches_valid)},
        "status": "IMPORTED" if lines_valid is not None else "INCOMPLETE",
        "limitations": [
            "A missing metric is unknown/unavailable, not zero coverage.",
            "Coverage measures execution, not correctness or completeness of assertions.",
            "Confirm the producer's format and scope before comparing reports across tools.",
        ],
    }
