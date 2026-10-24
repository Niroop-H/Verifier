"""Integrity-checked evidence bundle export and verification.

This provides tamper-evidence for accidental or post-export changes. It does not
prove who created a bundle unless a separate trusted signature/identity process
is configured, and it does not validate the underlying EDA result.
"""
from __future__ import annotations

import hashlib
import json
import os
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

BUNDLE_SCHEMA = "mqv-aegis-evidence-bundle/1.0"
MANIFEST_NAME = "evidence-manifest.json"
EXCLUDED_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules"}
MAX_FILES = 100_000
MAX_UNCOMPRESSED_BYTES = 2 * 1024 * 1024 * 1024

def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def _safe_relpath(name: str) -> str:
    p = PurePosixPath(name)
    if p.is_absolute() or not p.parts or any(part in ("", ".", "..") for part in p.parts):
        raise ValueError(f"Unsafe bundle path: {name!r}")
    if "\\" in name or "\x00" in name:
        raise ValueError(f"Unsafe bundle path: {name!r}")
    return p.as_posix()

def _files(root: Path) -> list[Path]:
    result = []
    for path in root.rglob("*"):
        if any(part in EXCLUDED_DIRS for part in path.relative_to(root).parts):
            continue
        if path.is_symlink():
            raise ValueError(f"Symlinks are not allowed in evidence bundles: {path}")
        if path.is_file():
            result.append(path)
            if len(result) > MAX_FILES:
                raise ValueError(f"Evidence bundle exceeds {MAX_FILES} files")
    return sorted(result, key=lambda p: p.relative_to(root).as_posix())

def create_bundle(source: Path, output: Path, *, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create ZIP evidence bundle with per-file SHA-256 and a deterministic manifest."""
    source = Path(source).resolve()
    output = Path(output).resolve()
    if not source.is_dir():
        raise ValueError("Evidence source must be a directory")
    if output == source or source in output.parents:
        raise ValueError("Bundle output must not be inside the source evidence directory")
    files = _files(source)
    total = sum(p.stat().st_size for p in files)
    if total > MAX_UNCOMPRESSED_BYTES:
        raise ValueError(f"Evidence bundle exceeds {MAX_UNCOMPRESSED_BYTES} uncompressed bytes")
    entries = []
    for path in files:
        rel = _safe_relpath(path.relative_to(source).as_posix())
        entries.append({"path": rel, "size_bytes": path.stat().st_size, "sha256": _sha256(path)})
    manifest = {
        "schema": BUNDLE_SCHEMA,
        "hash_algorithm": "sha256",
        "file_count": len(entries),
        "total_uncompressed_bytes": total,
        "metadata": metadata or {},
        "files": entries,
        "limitations": [
            "Hashes detect file changes relative to this manifest; the manifest itself is not signed.",
            "Integrity does not establish author identity, tool correctness, or fabrication readiness.",
            "Do not include classified or restricted data unless the destination and handling process are approved.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as archive:
        # Fixed ZIP metadata makes identical evidence content produce identical
        # archive bytes across runs (subject to the same Python/zlib behavior).
        for path in files:
            name = path.relative_to(source).as_posix()
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
        manifest_info = zipfile.ZipInfo(MANIFEST_NAME, date_time=(1980, 1, 1, 0, 0, 0))
        manifest_info.compress_type = zipfile.ZIP_DEFLATED
        manifest_info.external_attr = 0o100644 << 16
        archive.writestr(manifest_info, json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                         compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
    return {"archive": str(output), "sha256": _sha256(output), "file_count": len(entries),
            "total_uncompressed_bytes": total, "manifest": manifest}

def verify_bundle(bundle: Path) -> dict[str, Any]:
    """Verify member paths, limits, manifest structure, sizes, and SHA-256 digests."""
    bundle = Path(bundle)
    problems: list[str] = []
    checked = 0
    try:
        with zipfile.ZipFile(bundle, "r") as archive:
            infos = archive.infolist()
            if len(infos) > MAX_FILES + 1:
                raise ValueError("Bundle has too many archive entries")
            names = [info.filename for info in infos]
            if len(names) != len(set(names)):
                problems.append("Archive contains duplicate member names")
            total = 0
            for info in infos:
                try:
                    _safe_relpath(info.filename)
                except ValueError as exc:
                    problems.append(str(exc))
                if info.is_dir():
                    continue
                total += info.file_size
                if info.file_size > MAX_UNCOMPRESSED_BYTES or total > MAX_UNCOMPRESSED_BYTES:
                    raise ValueError("Bundle exceeds uncompressed size limits")
            if MANIFEST_NAME not in names:
                raise ValueError(f"Missing {MANIFEST_NAME}")
            manifest = json.loads(archive.read(MANIFEST_NAME))
            if manifest.get("schema") != BUNDLE_SCHEMA or manifest.get("hash_algorithm") != "sha256":
                raise ValueError("Unsupported evidence manifest schema or hash algorithm")
            declared = manifest.get("files")
            if not isinstance(declared, list):
                raise ValueError("Manifest files must be an array")
            declared_names = [entry.get("path") for entry in declared if isinstance(entry, dict)]
            actual_names = set(names) - {MANIFEST_NAME}
            if len(declared_names) != len(declared) or len(declared_names) != len(set(declared_names)):
                problems.append("Manifest contains invalid or duplicate file entries")
            if set(declared_names) != actual_names:
                problems.append("Manifest file list does not match archive contents")
            for entry in declared:
                if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
                    continue
                name = entry["path"]
                if name not in actual_names:
                    continue
                data = archive.read(name)
                if entry.get("size_bytes") != len(data):
                    problems.append(f"Size mismatch: {name}")
                digest = hashlib.sha256(data).hexdigest()
                if entry.get("sha256") != digest:
                    problems.append(f"SHA-256 mismatch: {name}")
                checked += 1
            if manifest.get("file_count") != len(declared):
                problems.append("Manifest file_count does not match files array")
            declared_total = sum(entry.get("size_bytes", -1) for entry in declared
                                 if isinstance(entry, dict) and isinstance(entry.get("size_bytes"), int))
            if manifest.get("total_uncompressed_bytes") != declared_total:
                problems.append("Manifest total_uncompressed_bytes does not match declared file sizes")
            archive_total = sum(info.file_size for info in infos
                                if not info.is_dir() and info.filename != MANIFEST_NAME)
            if manifest.get("total_uncompressed_bytes") != archive_total:
                problems.append("Manifest total_uncompressed_bytes does not match archive contents")
    except (OSError, zipfile.BadZipFile, json.JSONDecodeError, KeyError, RuntimeError, ValueError) as exc:
        return {"schema": BUNDLE_SCHEMA, "status": "INVALID", "checked_files": checked,
                "problems": problems + [str(exc)], "archive_sha256": _sha256(bundle) if bundle.is_file() else None}
    return {"schema": BUNDLE_SCHEMA, "status": "PASS" if not problems else "INVALID",
            "checked_files": checked, "problems": problems, "archive_sha256": _sha256(bundle),
            "limitations": [
                "PASS means listed file hashes match the included manifest only.",
                "The manifest is unsigned; use a trusted signature system to establish publisher identity.",
                "This does not prove the correctness or completeness of engineering results.",
            ]}
