from pathlib import Path
import sys
from mqv_eda.engine import execute_check, module_names, project_files, quote_yosys, looks_like_testbench
from mqv_eda.models import Status

def test_project_files_ignores_build_dirs(tmp_path):
    (tmp_path / "top.v").write_text("module top; endmodule\n")
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "junk.v").write_text("module junk; endmodule\n")
    assert [p.name for p in project_files(tmp_path, {".v"})] == ["top.v"]

def test_module_names(tmp_path):
    p = tmp_path / "top.sv"
    p.write_text("module automatic top(input logic a); endmodule\nmodule helper; endmodule\n")
    assert module_names([p]) == ["helper", "top"]

def test_yosys_path_quoted(tmp_path):
    p = tmp_path / "folder with spaces" / "top.v"
    p.parent.mkdir()
    p.write_text("module top; endmodule\n")
    assert quote_yosys(p).startswith('"')

def test_testbench_recognized():
    assert looks_like_testbench(Path("tb_top.sv"))
    assert looks_like_testbench(Path("core_tb.v"))
    assert not looks_like_testbench(Path("top.sv"))


def test_execute_check_timeout_is_inconclusive_and_logs_timeout(tmp_path):
    result = execute_check(
        "TIMEOUT_TEST",
        [sys.executable, "-c", "import time; time.sleep(5)"],
        required=True,
        inputs=[],
        output_dir=tmp_path,
        timeout=0.1,
    )
    assert result.status == Status.INCONCLUSIVE
    assert "timed out" in result.message.lower()
    assert "[TIMEOUT" in Path(result.log_path).read_text(encoding="utf-8")


def test_execute_check_bounds_output_and_fails_closed(tmp_path):
    result = execute_check(
        "OUTPUT_LIMIT_TEST",
        [sys.executable, "-c", "import sys; sys.stdout.write('x' * (6 * 1024 * 1024))"],
        required=True,
        inputs=[],
        output_dir=tmp_path,
        timeout=10,
    )
    log = Path(result.log_path).read_text(encoding="utf-8")
    assert result.status == Status.INCONCLUSIVE
    assert len(log.encode("utf-8")) <= 5 * 1024 * 1024 + 128
    assert "OUTPUT TRUNCATED" in log
    assert result.metadata["output_truncated"] is True
