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
    rows = []
    for result in results:
        rows.append("<tr><td>{}</td><td><strong>{}</strong></td><td>{}</td><td>{}</td></tr>".format(
            html.escape(result.stage), html.escape(result.status.value),
            html.escape("Required" if result.required else "Optional"),
            html.escape(result.message)))
    body = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>MAH Quantum Verify - EDA Evidence</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{font-family:system-ui,-apple-system,Segoe UI,sans-serif;max-width:1100px;margin:32px auto;padding:0 20px;color:#202631}
h1{font-size:1.7rem} .summary{padding:14px;border:1px solid #d5dbe3;border-radius:8px}
table{border-collapse:collapse;width:100%;margin-top:20px}th,td{border-bottom:1px solid #dfe3e8;text-align:left;padding:10px;vertical-align:top}
th{background:#f5f7fa} footer{margin-top:28px;color:#5c6675;font-size:.9rem}
</style></head><body><h1>MAH Quantum Verify — EDA Evidence</h1>
<div class="summary"><strong>Overall status: """ + html.escape(summary.value) + """</strong><br>
Generated: """ + html.escape(document["generated_utc"]) + """</div>
<table><thead><tr><th>Stage</th><th>Result</th><th>Requirement</th><th>Details</th></tr></thead><tbody>""" + "".join(rows) + """</tbody></table>
<footer>Evidence describes the named checks only. This report is not foundry sign-off, certification, or fabrication approval.</footer></body></html>"""
    html_path = output_dir / "report.html"
    html_path.write_text(body, encoding="utf-8")
    return {"json": json_path, "html": html_path}
