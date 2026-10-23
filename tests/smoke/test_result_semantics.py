from enum import Enum
class Status(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    INCONCLUSIVE = "INCONCLUSIVE"
    NOT_RUN = "NOT RUN"
    ERROR = "ERROR"

def aggregate(checks):
    """PASS overall only when all required checks actually passed."""
    required = [c for c in checks if c.get("required", True)]
    if not required:
        return Status.NOT_RUN
    states = [c.get("status") for c in required]
    if Status.ERROR in states:
        return Status.ERROR
    if Status.FAIL in states:
        return Status.FAIL
    if Status.BLOCKED in states:
        return Status.BLOCKED
    if Status.INCONCLUSIVE in states:
        return Status.INCONCLUSIVE
    if Status.NOT_RUN in states:
        return Status.NOT_RUN
    if all(s == Status.PASS for s in states):
        return Status.PASS
    return Status.ERROR

def test_missing_tool_never_passes():
    assert aggregate([{"status": Status.BLOCKED}]) == Status.BLOCKED

def test_one_fail_means_fail():
    assert aggregate([{"status": Status.PASS}, {"status": Status.FAIL}]) == Status.FAIL

def test_incomplete_suite_does_not_pass():
    assert aggregate([{"status": Status.PASS}, {"status": Status.NOT_RUN}]) == Status.NOT_RUN

def test_empty_suite_is_not_run():
    assert aggregate([]) == Status.NOT_RUN

def test_nonrequired_check_does_not_change_summary():
    assert aggregate([{"status": Status.PASS}, {"status": Status.BLOCKED, "required": False}]) == Status.PASS
