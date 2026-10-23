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


def test_zip_symlink_entry_rejected(tmp_path):
    import stat

    archive = tmp_path / "symlink.zip"
    info = zipfile.ZipInfo("project/link")
    info.create_system = 3
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr(info, "../../outside")
    with pytest.raises(UnsafeArchiveError, match="Symlink"):
        safe_extract_zip(archive, tmp_path / "out")


def test_zip_uncompressed_size_limit_rejected(tmp_path):
    archive = tmp_path / "large.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("large.txt", "A" * 4096)
    with pytest.raises(UnsafeArchiveError, match="uncompressed size"):
        safe_extract_zip(archive, tmp_path / "out", max_uncompressed_bytes=1024)


def test_zip_compression_ratio_limit_rejected(tmp_path):
    archive = tmp_path / "ratio.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("large.txt", "A" * (2 * 1024 * 1024))
    with pytest.raises(UnsafeArchiveError, match="compression ratio"):
        safe_extract_zip(archive, tmp_path / "out", max_compression_ratio=2)


def test_existing_destination_symlink_cannot_escape(tmp_path):
    archive = tmp_path / "symlink-target.zip"
    outside = tmp_path / "outside"
    outside.mkdir()
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("link/escape.txt", "bad")
    out = tmp_path / "out"
    out.mkdir()
    try:
        (out / "link").symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation is unavailable on this platform")
    with pytest.raises(UnsafeArchiveError):
        safe_extract_zip(archive, out)
    assert not (outside / "escape.txt").exists()
