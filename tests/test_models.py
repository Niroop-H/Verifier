from mahqv_eda.models import EdaResult, Status

def test_result_serialization_uses_stable_status_string():
    result = EdaResult(check="lint", status=Status.PASS, message="ok", command=["verilator"])
    assert result.to_dict()["status"] == "PASS"

def test_missing_tool_is_blocked_not_pass():
    from mahqv_eda.engine import run_command
    result = run_command("missing", ["mqv-tool-that-should-not-exist-12345"])
    assert result.status == Status.BLOCKED
    assert result.return_code is None

def test_timeout_is_inconclusive_not_pass():
    import sys
    from mahqv_eda.engine import run_command
    result = run_command("timeout", [sys.executable, "-c", "import time; time.sleep(2)"], timeout=0.05)
    assert result.status == Status.INCONCLUSIVE
