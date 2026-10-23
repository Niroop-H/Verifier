import os
from pathlib import Path
import subprocess


def test_isolated_runner_applies_container_restrictions(tmp_path):
    if os.name != "posix":
        return

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    args_file = tmp_path / "docker-args.txt"
    docker_stub = bin_dir / "docker"
    docker_stub.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"image\" ]; then exit 0; fi\n"
        "printf '%s\\n' \"$@\" > \"$MQV_DOCKER_ARGS_FILE\"\n",
        encoding="utf-8",
    )
    docker_stub.chmod(0o755)
    inputs = tmp_path / "inputs"
    outputs = tmp_path / "outputs"
    inputs.mkdir()
    outputs.mkdir()

    result = subprocess.run(
        [
            "bash",
            "scripts/run_isolated_job.sh",
            "test-worker:local",
            str(inputs),
            str(outputs),
            "--",
            "python3",
            "-c",
            "print('smoke')",
        ],
        env={
            **os.environ,
            "PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}",
            "MQV_DOCKER_ARGS_FILE": str(args_file),
        },
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    args = args_file.read_text(encoding="utf-8").splitlines()
    for required in (
        "--pull=never",
        "--network=none",
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges:true",
        "--pids-limit=128",
        "--memory=4g",
        "--memory-swap=4g",
        "--cpus=2",
        "--ulimit=fsize=1073741824:1073741824",
        "--ulimit=nofile=1024:1024",
    ):
        assert required in args
    assert "--mount" in args
    assert any("dst=/input,readonly" in arg for arg in args)
    assert any("dst=/output" in arg for arg in args)
    assert "--user=0:0" not in args
