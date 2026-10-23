from mqv_eda.models import CheckResult, Status, aggregate_status

def result(status, required=True):
    return CheckResult("test", status, "test", required=required)

def test_all_required_pass():
    assert aggregate_status([result(Status.PASS), result(Status.PASS)]) == Status.PASS

def test_fail_closed_for_blocked():
    assert aggregate_status([result(Status.PASS), result(Status.BLOCKED)]) == Status.BLOCKED

def test_failure_not_hidden_by_pass():
    assert aggregate_status([result(Status.PASS), result(Status.FAIL)]) == Status.FAIL

def test_error_has_priority():
    assert aggregate_status([result(Status.FAIL), result(Status.ERROR)]) == Status.ERROR

def test_optional_not_run_does_not_block():
    assert aggregate_status([result(Status.PASS), result(Status.NOT_RUN, required=False)]) == Status.PASS

def test_empty_required_set_not_pass():
    assert aggregate_status([result(Status.NOT_RUN, required=False)]) == Status.NOT_RUN
