from mqv_eda.models import CheckResult, Status
from mqv_eda.reporting import write_reports


def test_html_report_has_accessible_semantics_counts_and_escaped_text(tmp_path):
    outputs = write_reports(tmp_path, [
        CheckResult("lint <rtl>", Status.PASS, "Clean & valid", required=True),
        CheckResult("simulation", Status.BLOCKED, "Tool unavailable", required=True),
    ])
    html = outputs["html"].read_text(encoding="utf-8")
    assert '<html lang="en">' in html
    assert '<caption>Individual check results</caption>' in html
    assert 'scope="col"' in html and 'scope="row"' in html
    assert 'aria-labelledby="run-summary-heading"' in html
    assert "Check counts" in html
    assert "Clean &amp; valid" in html
    assert "lint &lt;rtl&gt;" in html
    assert ":focus-visible" in html
    assert "@media print" in html
    assert "fabrication approval" in html
