import subprocess
import sys
from pathlib import Path


def test_run_canonical_requires_backend():
    p = subprocess.run(
        [sys.executable, "scripts/qualification/run-canonical.py"],
        capture_output=True,
        text=True,
    )
    assert p.returncode != 0


def test_run_canonical_unknown_backend_fails():
    p = subprocess.run(
        [
            sys.executable,
            "scripts/qualification/run-canonical.py",
            "--backend",
            "gpu9",
        ],
        capture_output=True,
        text=True,
    )
    assert p.returncode != 0


def test_package_evidence_rejects_present_secret(tmp_path: Path):
    evidence = tmp_path / "ev"
    evidence.mkdir()
    secret = "token=" + "g" + "hp_" + "1234567890abcdef\n"
    (evidence / "note.txt").write_text(secret)
    output = tmp_path / "pkg"
    p = subprocess.run(
        [
            sys.executable,
            "scripts/qualification/package-evidence.py",
            "--evidence-root",
            str(evidence),
            "--output",
            str(output),
            "--label",
            "linux-cpu",
        ],
        capture_output=True,
        text=True,
    )
    assert p.returncode == 2
    assert "SECRET_SCAN=FAIL" in p.stdout


def test_package_evidence_ok_with_no_secrets(tmp_path: Path):
    evidence = tmp_path / "ev"
    evidence.mkdir()
    (evidence / "result.json").write_text('{"ok": true}\n')
    output = tmp_path / "pkg"
    p = subprocess.run(
        [
            sys.executable,
            "scripts/qualification/package-evidence.py",
            "--evidence-root",
            str(evidence),
            "--output",
            str(output),
            "--label",
            "linux-cpu",
        ],
        capture_output=True,
        text=True,
    )
    assert p.returncode == 0
    assert "SECRET_SCAN=PASS" in p.stdout


def test_local_layout_proof_requires_all_three():
    p = subprocess.run(
        ["bash", "scripts/qualification/run-local-layout-proof.sh", "--dit", "a"],
        capture_output=True,
        text=True,
    )
    assert p.returncode != 0


def test_local_layout_proof_syntax_is_valid():
    p = subprocess.run(
        ["bash", "-n", "scripts/qualification/run-local-layout-proof.sh"],
        capture_output=True,
        text=True,
    )
    assert p.returncode == 0


def test_qualification_evidence_records_filename_and_sha256_explicitly():
    producers = (
        (
            Path("integrations/kaggle/qualification.py"),
            "manifest_with_root",
        ),
        (
            Path("scripts/qualification/run-canonical.py"),
            "manifest",
        ),
    )

    for path, manifest_name in producers:
        source = path.read_text(encoding="utf-8")
        assert '"model_hashes"' not in source
        assert '"models": {' in source
        assert '"filename": verified["diffusion"].name' in source
        assert '"filename": verified["text_encoder"].name' in source
        assert '"filename": verified["vae"].name' in source
        assert f'"sha256": {manifest_name}.diffusion.sha256' in source
        assert f'"sha256": {manifest_name}.text_encoder.sha256' in source
        assert f'"sha256": {manifest_name}.vae.sha256' in source
