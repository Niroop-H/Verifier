import json
import zipfile
from pathlib import Path
from mqv_eda.evidence_bundle import create_bundle, verify_bundle, MANIFEST_NAME

def test_bundle_roundtrip_and_hashes(tmp_path):
    source=tmp_path/"evidence"; source.mkdir()
    (source/"report.json").write_text('{"overall_status":"PASS"}')
    (source/"logs").mkdir()
    (source/"logs"/"sim.log").write_text("simulation complete\n")
    out=tmp_path/"bundle.zip"
    created=create_bundle(source,out,metadata={"project":"fixture"})
    verified=verify_bundle(out)
    assert created["file_count"] == 2
    assert verified["status"] == "PASS"
    assert verified["checked_files"] == 2

def test_bundle_detects_tampered_member(tmp_path):
    source=tmp_path/"evidence"; source.mkdir()
    (source/"report.json").write_text("original")
    out=tmp_path/"bundle.zip"
    create_bundle(source,out)
    changed=tmp_path/"tampered.zip"
    with zipfile.ZipFile(out) as zin, zipfile.ZipFile(changed,"w") as zout:
        for info in zin.infolist():
            data=zin.read(info.filename)
            if info.filename == "report.json":
                data=b"changed"
            zout.writestr(info.filename,data)
    result=verify_bundle(changed)
    assert result["status"] == "INVALID"
    assert any("mismatch" in p.lower() for p in result["problems"])

def test_bundle_rejects_symlinks(tmp_path):
    source=tmp_path/"evidence"; source.mkdir()
    target=tmp_path/"secret.txt"; target.write_text("secret")
    link=source/"link.txt"
    try:
        link.symlink_to(target)
    except OSError:
        return
    import pytest
    with pytest.raises(ValueError, match="Symlinks"):
        create_bundle(source,tmp_path/"bundle.zip")

def test_bundle_rejects_traversal_member(tmp_path):
    bad=tmp_path/"bad.zip"
    with zipfile.ZipFile(bad,"w") as z:
        z.writestr("../escape.txt","bad")
    result=verify_bundle(bad)
    assert result["status"] == "INVALID"
    assert any("Unsafe" in p for p in result["problems"])


def test_bundle_creation_is_reproducible_for_same_evidence(tmp_path):
    source = tmp_path / "evidence"
    source.mkdir()
    (source / "report.json").write_text('{"status":"PASS"}')
    (source / "logs").mkdir()
    (source / "logs" / "run.log").write_text("finished\\n")
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"
    create_bundle(source, first, metadata={"project": "fixture"})
    create_bundle(source, second, metadata={"project": "fixture"})
    assert first.read_bytes() == second.read_bytes()


def test_bundle_rejects_manifest_total_size_tampering(tmp_path):
    source = tmp_path / "evidence"
    source.mkdir()
    (source / "report.json").write_text("abc")
    bundle = tmp_path / "bundle.zip"
    create_bundle(source, bundle)
    changed = tmp_path / "changed.zip"
    with zipfile.ZipFile(bundle) as zin, zipfile.ZipFile(changed, "w") as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename == MANIFEST_NAME:
                manifest = json.loads(data)
                manifest["total_uncompressed_bytes"] += 10
                data = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
            zout.writestr(info, data)
    result = verify_bundle(changed)
    assert result["status"] == "INVALID"
    assert any("total_uncompressed_bytes" in problem for problem in result["problems"])
