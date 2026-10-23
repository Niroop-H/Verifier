from pathlib import Path
import subprocess
import sys
import json

def test_environment_discovery_reports_json():
    root = Path(__file__).resolve().parents[2]
    p = subprocess.run([sys.executable, str(root / "scripts" / "check_environment.py")],
                       cwd=root, check=True, text=True, capture_output=True)
    data = json.loads(p.stdout)
    assert "tools" in data
    assert "iverilog" in data["tools"]
    assert data["tools"]["iverilog"]["state"] in {"AVAILABLE", "BLOCKED", "ERROR"}
