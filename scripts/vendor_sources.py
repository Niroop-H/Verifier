#!/usr/bin/env python3
"""Materialize pinned upstream source snapshots into the main repository.

Snapshots contain source files (including upstream notices), not nested Git
repositories. A small provenance marker records the exact origin/revision and a
deterministic digest so the outer MAH Quantum Verify repository can track them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "vendor" / "manifest.json"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
MARKER = ".mqv-vendor-provenance.json"


def load_manifest() -> dict[str, Any]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("Unsupported vendor manifest schema_version")
    if not isinstance(data.get("sources"), list):
        raise ValueError("manifest.sources must be a list")
    seen: set[str] = set()
    destinations: set[Path] = set()
    for item in data["sources"]:
        name = item.get("name", "")
        destination = item.get("destination", "")
        revision = item.get("revision", "")
        repository = item.get("repository", "")
        if not name or name in seen:
            raise ValueError(f"Missing or duplicate source name: {name!r}")
        seen.add(name)
        if not HEX40.fullmatch(revision):
            raise ValueError(f"{name}: revision must be a full 40-character commit SHA")
        if not repository.startswith("https://"):
            raise ValueError(f"{name}: repository must use HTTPS")
        if not destination.startswith("vendor/src/"):
            raise ValueError(f"{name}: source destination must be under vendor/src/")
        dest = (ROOT / destination).resolve()
        if ROOT not in dest.parents:
            raise ValueError(f"{name}: destination escapes repository root")
        if dest in destinations:
            raise ValueError(f"{name}: duplicate destination")
        destinations.add(dest)
    return data


def run(args: list[str], *, cwd: Path | None = None) -> str:
    proc = subprocess.run(args, cwd=cwd, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, text=True, check=False)
    if proc.returncode:
        raise RuntimeError(f"Command failed ({proc.returncode}): {args!r}\n{proc.stdout[-5000:]}")
    return proc.stdout.strip()


def git_available() -> None:
    if not shutil.which("git"):
        raise RuntimeError("Git is required for source synchronization and verification.")


def tree_digest(root: Path) -> str:
    """Hash paths, file bytes, executable bits and symlink targets deterministically."""
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix()):
        if path.name == MARKER:
            continue
        relative = path.relative_to(root).as_posix().encode("utf-8", errors="surrogateescape")
        if path.is_symlink():
            kind = b"L"
            payload = os.readlink(path).encode("utf-8", errors="surrogateescape")
            executable = b""
        elif path.is_dir():
            kind, payload, executable = b"D", b"", b""
        elif path.is_file():
            kind = b"F"
            payload = path.read_bytes()
            executable = b"x" if path.stat().st_mode & 0o111 else b"-"
        else:
            raise RuntimeError(f"Unsupported special file in source snapshot: {path}")
        digest.update(kind + b"\0" + relative + b"\0" + executable + b"\0")
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def read_marker(destination: Path) -> dict[str, Any] | None:
    path = destination / MARKER
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def sync(item: dict[str, Any]) -> None:
    destination = ROOT / item["destination"]
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        marker = read_marker(destination)
        if not marker or marker.get("repository") != item["repository"] or marker.get("revision") != item["revision"]:
            raise RuntimeError(f"Refusing to overwrite unrecognized or differently pinned directory: {destination}")
        if marker.get("tree_sha256") != tree_digest(destination):
            raise RuntimeError(f"Refusing to overwrite modified source snapshot: {destination}")
        shutil.rmtree(destination)

    with tempfile.TemporaryDirectory(prefix="mqv-vendor-") as temporary:
        checkout = Path(temporary) / "checkout"
        run(["git", "clone", "--no-checkout", item["repository"], str(checkout)])
        # Explicitly request the full commit so it is not dependent on the default branch name.
        run(["git", "fetch", "origin", item["revision"]], cwd=checkout)
        run(["git", "checkout", "--detach", item["revision"]], cwd=checkout)
        actual = run(["git", "rev-parse", "HEAD"], cwd=checkout)
        if actual != item["revision"]:
            raise RuntimeError(f"{item['name']}: requested {item['revision']}, got {actual}")
        shutil.copytree(checkout, destination, symlinks=True,
                        ignore=shutil.ignore_patterns(".git"))
    digest = tree_digest(destination)
    marker = {
        "schema_version": 1,
        "name": item["name"],
        "repository": item["repository"],
        "revision": item["revision"],
        "tree_sha256": digest,
        "license_review": item.get("license_review", "required"),
        "notice": "Upstream source. Preserve original license and copyright terms."
    }
    (destination / MARKER).write_text(json.dumps(marker, indent=2) + "\n", encoding="utf-8")
    print(f"SNAPSHOTTED {item['name']} commit={actual} tree_sha256={digest} -> {item['destination']}")


def verify(item: dict[str, Any]) -> bool:
    destination = ROOT / item["destination"]
    marker = read_marker(destination)
    if not marker:
        print(f"MISSING/INVALID {item['name']}: run vendor_sources.py sync")
        return False
    actual_digest = tree_digest(destination)
    expected = (
        marker.get("schema_version") == 1
        and marker.get("name") == item["name"]
        and marker.get("repository") == item["repository"]
        and marker.get("revision") == item["revision"]
        and marker.get("tree_sha256") == actual_digest
    )
    print(f"{'OK' if expected else 'MISMATCH'} {item['name']} revision={marker.get('revision')} tree_sha256={actual_digest}")
    return expected


def verify_artifact(item: dict[str, Any]) -> bool:
    path = ROOT / item["destination"]
    if not path.is_file():
        print(f"MISSING ARTIFACT {item['name']}: {path.relative_to(ROOT)}")
        return False
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    ok = digest == item["sha256"]
    print(f"{'OK' if ok else 'HASH MISMATCH'} {item['name']} sha256={digest}")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("sync", "verify", "status"))
    parser.add_argument("--name", help="Operate on one named source or binary artifact")
    ns = parser.parse_args()
    try:
        manifest = load_manifest()
        sources = [x for x in manifest["sources"] if not ns.name or x["name"] == ns.name]
        artifacts = [x for x in manifest.get("binary_artifacts", []) if not ns.name or x["name"] == ns.name]
        if ns.name and not sources and not artifacts:
            parser.error(f"Unknown dependency name: {ns.name}")
        if ns.command == "sync":
            git_available()
            for item in sources:
                sync(item)
            if artifacts:
                print("Binary artifact download is intentionally not implemented here; acquire it through an approved process, then place it at the manifest destination and run verify.")
            return 0
        if ns.command == "verify":
            results = [verify(item) for item in sources]
            results.extend(verify_artifact(item) for item in artifacts)
            return 0 if all(results) else 1
        for item in sources:
            print(f"SOURCE {item['name']} revision={item['revision']} destination={item['destination']} license_review={item['license_review']}")
        for item in artifacts:
            print(f"ARTIFACT {item['name']} version={item['version']} sha256={item['sha256']} destination={item['destination']} license_review={item['license_review']}")
        print("Status lists the pinned plan; use sync to materialize source files and verify to check local snapshots.")
        return 0
    except (OSError, ValueError, json.JSONDecodeError, RuntimeError) as exc:
        print(f"vendor_sources: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
