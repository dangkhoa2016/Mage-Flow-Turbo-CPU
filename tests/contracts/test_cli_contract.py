import subprocess
import sys


def test_cli_help_exposes_required_commands():
    p = subprocess.run(
        [sys.executable, "-m", "mageflow_native.cli", "--help"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert p.returncode == 0
    for command in ("doctor", "verify", "generate", "serve", "runtime"):
        assert command in p.stdout
