import zipfile
from pathlib import Path
import pytest
from mqv_eda.security import safe_extract_zip, UnsafeArchiveError, sha256_file

def test_safe_zip_extracts_file(tmp_path):
    archive = tmp_path / "safe.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("project/top.v", "module top; endmodule\n")
    out = safe_extract_zip(archive, tmp_path / "out")
    assert (out / "project" / "top.v").read_text() == "module top; endmodule\n"

@pytest.mark.parametrize("name", ["../escape.txt", "/tmp/escape.txt", "C:/escape.txt", r"..\\escape.txt"])
def test_zip_path_traversal_rejected(tmp_path, name):
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr(name, "bad")
    with pytest.raises(UnsafeArchiveError):
        safe_extract_zip(archive, tmp_path / "out")

def test_max_entry_limit(tmp_path):
    archive = tmp_path / "many.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("a", "1")
        z.writestr("b", "2")
    with pytest.raises(UnsafeArchiveError):
        safe_extract_zip(archive, tmp_path / "out", max_files=1)

def test_sha256_is_stable(tmp_path):
    p = tmp_path / "x"
    p.write_bytes(b"abc")
    assert sha256_file(p) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
