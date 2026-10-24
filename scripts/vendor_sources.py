#!/usr/bin/env python3
"""Synchronize and verify pinned upstream source snapshots.

This tool deliberately vendors complete Git repositories at immutable commit IDs.
It does not rewrite upstream license/copyright files and does not download anything
during MAH Quantum Verify runtime. Run from the repository root.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "vendor" / "manifest.json"
HEX40 = re.compile(r"^[0-9a-f]{40}$")


def load_manifest() -> dict[str, Any]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("Unsupported vendor manifest schema_version")
    if not isinstance(data.get("sources"), list):
        raise ValueError("manifest.sources must be a list")
    seen: set[str] = set()
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
        dest = (ROOT / destination).resolve()
        if ROOT not in dest.parents:
            raise ValueError(f"{name}: destination escapes repository root")
        if not destination.startswith("vendor/src/"):
            raise ValueError(f"{name}: source destination must be under vendor/src/")
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


def sync(item: dict[str, Any]) -> None:
    destination = ROOT / item["destination"]
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if not (destination / ".git").is_dir():
            raise RuntimeError(f"Refusing to overwrite non-Git directory: {destination}")
        origin = run(["git", "remote", "get-url", "origin"], cwd=destination)
        if origin.rstrip("/") != item["repository"].rstrip("/"):
            raise RuntimeError(f"{destination}: origin mismatch ({origin})")
        dirty = run(["git", "status", "--porcelain"], cwd=destination)
        if dirty:
            raise RuntimeError(f"Refusing to overwrite dirty source tree: {destination}")
        run(["git", "fetch", "--tags", "origin"], cwd=destination)
    else:
        run(["git", "clone", "--no-checkout", item["repository"], str(destination)])
    run(["git", "cat-file", "-e", f"{item['revision']}^{{commit}}"], cwd=destination)
    run(["git", "checkout", "--detach", item["revision"]], cwd=destination)
    actual = run(["git", "rev-parse", "HEAD"], cwd=destination)
    if actual != item["revision"]:
        raise RuntimeError(f"{item['name']}: requested {item['revision']}, got {actual}")
    print(f"SYNCED {item['name']} {actual} -> {item['destination']}")


def verify(item: dict[str, Any]) -> bool:
    destination = ROOT / item["destination"]
    if not (destination / ".git").is_dir():
        print(f"MISSING {item['name']}: run vendor_sources.py sync")
        return False
    try:
        origin = run(["git", "remote", "get-url", "origin"], cwd=destination)
        actual = run(["git", "rev-parse", "HEAD"], cwd=destination)
        dirty = run(["git", "status", "--porcelain"], cwd=destination)
    except RuntimeError as exc:
        print(f"ERROR {item['name']}: {exc}")
        return False
    ok = (
        origin.rstrip("/") == item["repository"].rstrip("/")
        and actual == item["revision"]
        and not dirty
    )
    print(f"{'OK' if ok else 'MISMATCH'} {item['name']} expected={item['revision']} actual={actual} dirty={bool(dirty)}")
    return ok


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
                print("Binary artifact download is intentionally not implemented here; obtain it through an approved acquisition process, then place it at the manifest destination and run verify.")
            return 0
        if ns.command == "verify":
            git_available()
            results = [verify(item) for item in sources]
            results.extend(verify_artifact(item) for item in artifacts)
            return 0 if all(results) else 1
        for item in sources:
            print(f"SOURCE {item['name']} revision={item['revision']} destination={item['destination']} license_review={item['license_review']}")
        for item in artifacts:
            print(f"ARTIFACT {item['name']} version={item['version']} sha256={item['sha256']} destination={item['destination']} license_review={item['license_review']}")
        print("Status lists the pinned plan; use verify to check local snapshots.")
        return 0
    except (OSError, ValueError, json.JSONDecodeError, RuntimeError) as exc:
        print(f"vendor_sources: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
