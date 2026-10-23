from pathlib import Path
import subprocess
import sys

def test_environment_discovery_reports_json():
    root = Path(__file__).resolve().parents[1]
    p = subprocess.run([sys.executable, str(root / "scripts/check_environment.py")],
                       cwd=root, check=True, text=True, capture_output=True)
    import json
    data = json.loads(p.stdout)
    assert "tools" in data
    assert "iverilog" in data["tools"]
    assert data["tools"]["iverilog"]["state"] in {"AVAILABLE", "BLOCKED", "ERROR"}
