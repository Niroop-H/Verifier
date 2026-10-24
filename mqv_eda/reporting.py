from __future__ import annotations
import html
import json
from pathlib import Path
from typing import Any
from .models import CheckResult, aggregate_status, utc_now

def write_reports(output_dir: Path, results: list[CheckResult], metadata: dict[str, Any] | None = None) -> dict[str, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = aggregate_status(results)
    document = {
        "schema_version": "1.0",
        "generated_utc": utc_now(),
        "product": "MAH Quantum Verify",
        "session": "Session 1 - EDA Verification",
        "overall_status": summary.value,
        "metadata": metadata or {},
        "checks": [result.to_dict() for result in results],
        "limitations": [
            "A PASS applies only to the named check and its supplied inputs.",
            "A smoke test is not foundry sign-off or fabrication readiness.",
            "Missing prerequisites and unexecuted checks are not counted as successful.",
        ],
    }
    json_path = output_dir / "report.json"
    json_path.write_text(json.dumps(document, indent=2, sort_keys=True), encoding="utf-8")
    counts: dict[str, int] = {}
    for result in results:
        counts[result.status.value] = counts.get(result.status.value, 0) + 1
    rows = []
    for result in results:
        status = html.escape(result.status.value)
        rows.append(
            '<tr><th scope="row">{stage}</th><td><span class="status">{status}</span></td>'
            '<td>{required}</td><td>{message}</td></tr>'.format(
                stage=html.escape(result.stage), status=status,
                required=html.escape("Required" if result.required else "Optional"),
                message=html.escape(result.message))
        )
    count_items = "".join(
        '<li><strong>{}</strong>: {}</li>'.format(html.escape(name), number)
        for name, number in sorted(counts.items())
    ) or "<li>No checks were recorded.</li>"
    body = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>MAH Quantum Verify - EDA Evidence</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light">
<style>
:root{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;color:#202631;background:#fff}
body{max-width:1100px;margin:32px auto;padding:0 20px;line-height:1.55}
h1{font-size:1.7rem;line-height:1.2}
.summary{padding:16px;border:1px solid #b8c2cf;border-radius:8px;margin:18px 0}
.summary h2{font-size:1.1rem;margin:0 0 8px}
.counts{display:flex;flex-wrap:wrap;gap:8px 28px;padding-left:20px}
table{border-collapse:collapse;width:100%;margin-top:20px}
caption{text-align:left;font-weight:700;padding:12px 0}
th,td{border-bottom:1px solid #dfe3e8;text-align:left;padding:10px;vertical-align:top}
thead th{background:#f5f7fa}
.status{font-weight:700}
a{color:#174ea6}
:focus-visible{outline:3px solid #174ea6;outline-offset:3px}
footer{margin-top:28px;color:#4b5563;font-size:.95rem}
@media(max-width:650px){body{margin:16px auto;padding:0 12px}table{font-size:.9rem}th,td{padding:7px}}
@media print{body{max-width:none;margin:0;padding:0}.summary{break-inside:avoid}table{font-size:9pt}}
</style></head><body>
<h1>MAH Quantum Verify — EDA Evidence</h1>
<p>Verification evidence summary for the checks executed on the supplied design and configuration.</p>
<section class="summary" aria-labelledby="run-summary-heading">
<h2 id="run-summary-heading">Run summary</h2>
<p><strong>Overall status: """ + html.escape(summary.value) + """</strong></p>
<p>Generated (UTC): """ + html.escape(document["generated_utc"]) + """</p>
<ul class="counts" aria-label="Check counts">""" + count_items + """</ul>
</section>
<table>
<caption>Individual check results</caption>
<thead><tr><th scope="col">Stage</th><th scope="col">Result</th><th scope="col">Requirement</th><th scope="col">Details</th></tr></thead>
<tbody>""" + "".join(rows) + """</tbody></table>
<footer><p>Evidence describes the named checks only. A passing check does not imply complete verification, foundry sign-off, certification, or fabrication approval. Missing prerequisites and unexecuted checks are not successful checks.</p></footer>
</body></html>"""
    html_path = output_dir / "report.html"
    html_path.write_text(body, encoding="utf-8")
    return {"json": json_path, "html": html_path}



def write_history_dashboard(history: dict[str, Any], output_path: Path) -> Path:
    """Render an accessible, script-free HTML dashboard from regression-history data."""
    if not isinstance(history, dict) or not isinstance(history.get("runs"), list):
        raise ValueError("history must contain a runs array")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    totals: dict[str, int] = {}
    for run in history["runs"]:
        if not isinstance(run, dict):
            continue
        counts = run.get("check_counts", {})
        if not isinstance(counts, dict):
            counts = {}
        for name, value in counts.items():
            if isinstance(value, int) and value >= 0:
                totals[name] = totals.get(name, 0) + value
        rows.append(
            "<tr><th scope=\"row\">{report}</th><td>{status}</td><td>{duration}</td><td>{counts}</td></tr>".format(
                report=html.escape(str(run.get("report", "UNKNOWN"))),
                status=html.escape(str(run.get("overall_status", "UNKNOWN"))),
                duration=html.escape(str(run.get("duration_seconds", 0))),
                counts=html.escape(", ".join(f"{k}: {v}" for k, v in sorted(counts.items()))),
            )
        )
    summary = "".join(
        "<li><strong>{}</strong>: {}</li>".format(html.escape(key), value)
        for key, value in sorted(totals.items())
    ) or "<li>No check results recorded.</li>"
    document = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MAH Quantum Verify — Regression Dashboard</title>
<style>
:root{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;color:#202631;background:#fff}
body{max-width:1200px;margin:32px auto;padding:0 20px;line-height:1.5}
h1{font-size:1.7rem}.summary{border:1px solid #b8c2cf;border-radius:10px;padding:16px;margin:20px 0}
ul{display:flex;flex-wrap:wrap;gap:8px 24px;padding-left:20px}
table{border-collapse:collapse;width:100%;margin-top:20px}caption{text-align:left;font-weight:700;padding:12px 0}
th,td{padding:10px;border-bottom:1px solid #dfe3e8;text-align:left;vertical-align:top}
thead th{background:#f5f7fa} :focus-visible{outline:3px solid #174ea6;outline-offset:3px}
footer{margin-top:24px;color:#4b5563;font-size:.95rem}
@media(max-width:700px){body{margin:16px auto;padding:0 12px}th,td{padding:7px;font-size:.9rem}}
@media(print){body{max-width:none;margin:0;padding:0}}
</style></head><body>
<h1>MAH Quantum Verify — Regression Dashboard</h1>
<p>Historical summary of supplied verification reports. Results are not independently rerun by this dashboard.</p>
<section class="summary" aria-labelledby="summary-heading"><h2 id="summary-heading">Aggregate check outcomes</h2>
<ul>""" + summary + """</ul></section>
<table><caption>Regression runs</caption><thead><tr><th scope="col">Report</th><th scope="col">Overall status</th><th scope="col">Duration (s)</th><th scope="col">Check counts</th></tr></thead>
<tbody>""" + "".join(rows) + """</tbody></table>
<footer>Historical aggregation only. A dashboard summary is not sign-off, certification, or fabrication-readiness evidence.</footer>
</body></html>"""
    output_path.write_text(document, encoding="utf-8")
    return output_path
