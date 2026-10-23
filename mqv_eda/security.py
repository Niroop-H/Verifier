from __future__ import annotations
import hashlib
import os
import re
import shutil
import stat
import zipfile
from pathlib import Path, PurePosixPath

class UnsafeArchiveError(ValueError):
    """Raised when an archive has unsafe paths, special files, or excessive size."""

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def safe_extract_zip(
    archive: Path,
    destination: Path,
    *,
    max_files: int = 10000,
    max_uncompressed_bytes: int = 2 * 1024 * 1024 * 1024,
    max_compression_ratio: int = 500,
) -> Path:
    """Extract a ZIP without permitting path traversal or archive-created symlinks."""
    archive = Path(archive)
    destination = Path(destination)
    if not zipfile.is_zipfile(archive):
        raise UnsafeArchiveError("Input is not a valid ZIP archive.")
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    seen: set[str] = set()
    total = 0
    with zipfile.ZipFile(archive) as zf:
        entries = zf.infolist()
        if len(entries) > max_files:
            raise UnsafeArchiveError(f"Archive contains too many entries ({len(entries)} > {max_files}).")
        for info in entries:
            raw_name = info.filename.replace("\\", "/")
            member = PurePosixPath(raw_name)
            if not raw_name or "\x00" in raw_name or member.is_absolute():
                raise UnsafeArchiveError(f"Unsafe archive path: {info.filename!r}")
            if any(part in ("..", "") for part in member.parts):
                raise UnsafeArchiveError(f"Path traversal in archive member: {info.filename!r}")
            if re.match(r"^[A-Za-z]:", raw_name) or raw_name.startswith("//"):
                raise UnsafeArchiveError(f"Absolute or drive-qualified path: {info.filename!r}")
            normalized = member.as_posix()
            if normalized in seen and not info.is_dir():
                raise UnsafeArchiveError(f"Duplicate file entry: {normalized}")
            seen.add(normalized)
            mode = (info.external_attr >> 16) & 0xFFFF
            kind = stat.S_IFMT(mode)
            if kind == stat.S_IFLNK:
                raise UnsafeArchiveError(f"Symlink entry is not allowed: {normalized}")
            if kind not in (0, stat.S_IFREG, stat.S_IFDIR):
                raise UnsafeArchiveError(f"Special file entry is not allowed: {normalized}")
            if info.file_size < 0:
                raise UnsafeArchiveError(f"Invalid size for {normalized}")
            total += info.file_size
            if total > max_uncompressed_bytes:
                raise UnsafeArchiveError("Archive exceeds maximum uncompressed size.")
            if info.file_size > 1024 * 1024 and info.compress_size > 0:
                if info.file_size / info.compress_size > max_compression_ratio:
                    raise UnsafeArchiveError(f"Suspicious compression ratio for {normalized}")
        for info in entries:
            normalized = info.filename.replace("\\", "/")
            member = PurePosixPath(normalized)
            target = root.joinpath(*member.parts)
            resolved_parent = target.parent.resolve()
            if not resolved_parent.is_relative_to(root):
                raise UnsafeArchiveError(f"Extraction target escapes destination: {normalized}")
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.resolve().is_relative_to(root):
                raise UnsafeArchiveError(f"Extraction target escapes destination: {normalized}")
            # Exclusive creation prevents duplicate entries overwriting a prior file.
            with zf.open(info, "r") as source, target.open("xb") as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)
    return destination
