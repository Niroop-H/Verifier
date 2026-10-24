from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "vendor_sources.py"
SPEC = importlib.util.spec_from_file_location("vendor_sources", MODULE_PATH)
assert SPEC and SPEC.loader
vendor_sources = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(vendor_sources)


def test_manifest_declares_only_full_commit_pins():
    data = vendor_sources.load_manifest()
    assert data["sources"]
    assert all(len(item["revision"]) == 40 for item in data["sources"])
    assert all(item["destination"].startswith("vendor/src/") for item in data["sources"])


def test_manifest_rejects_mutable_branch_or_tag(tmp_path, monkeypatch):
    manifest = {
        "schema_version": 1,
        "sources": [{
            "name": "example",
            "repository": "https://example.com/example.git",
            "revision": "main",
            "destination": "vendor/src/example"
        }]
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(vendor_sources, "MANIFEST", path)
    monkeypatch.setattr(vendor_sources, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="full 40-character commit SHA"):
        vendor_sources.load_manifest()


def test_manifest_rejects_destination_traversal(tmp_path, monkeypatch):
    manifest = {
        "schema_version": 1,
        "sources": [{
            "name": "example",
            "repository": "https://example.com/example.git",
            "revision": "a" * 40,
            "destination": "vendor/src/../../outside"
        }]
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(vendor_sources, "MANIFEST", path)
    monkeypatch.setattr(vendor_sources, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="escapes repository root"):
        vendor_sources.load_manifest()


def test_manifest_rejects_non_https_repository(tmp_path, monkeypatch):
    manifest = {
        "schema_version": 1,
        "sources": [{
            "name": "example",
            "repository": "git@example.com:example.git",
            "revision": "a" * 40,
            "destination": "vendor/src/example"
        }]
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(vendor_sources, "MANIFEST", path)
    monkeypatch.setattr(vendor_sources, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="must use HTTPS"):
        vendor_sources.load_manifest()
