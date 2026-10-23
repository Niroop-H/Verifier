from pathlib import Path
from mqv_eda.engine import module_names, project_files, quote_yosys, looks_like_testbench

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
