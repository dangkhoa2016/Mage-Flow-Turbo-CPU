import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class KaggleEntrypointTests(unittest.TestCase):
    def run_help(self, relative_path: str):
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        cp = subprocess.run(
            [sys.executable, str(ROOT / relative_path), "--help"],
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertNotIn("ModuleNotFoundError", cp.stderr + cp.stdout)

    def test_preflight_runs_directly_from_repo_root_without_pythonpath(self):
        self.run_help("scripts/kaggle/preflight.py")

    def test_local_acceptance_runs_directly_from_repo_root_without_pythonpath(self):
        self.run_help("scripts/kaggle/local_acceptance.py")


if __name__ == "__main__":
    unittest.main()
