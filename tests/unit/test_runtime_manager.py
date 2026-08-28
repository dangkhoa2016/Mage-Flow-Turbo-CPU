import os
from pathlib import Path

import pytest

from mageflow_native.runtime.manager import RuntimeManager


def _fake_sd_cli(path: Path, version: str, devices: str) -> None:
    script = (
        "#!/usr/bin/env python3\n"
        "import sys\n"
        f"if sys.argv[1] == '--version':\n"
        f"    print({version!r})\n"
        f"elif sys.argv[1] == '--list-devices':\n"
        f"    print({devices!r}, end='')\n"
    )
    path.write_text(script)
    path.chmod(0o755)


def test_resolve_explicit_path_takes_precedence(tmp_path: Path, monkeypatch):
    explicit = tmp_path / "my-sd-cli"
    _fake_sd_cli(explicit, "6b3edaa v1", "CPU\n")
    other = tmp_path / "other-sd-cli"
    (tmp_path / "bin").mkdir()
    _fake_sd_cli(tmp_path / "bin" / "sd-cli", "6b3edaa v1", "CPU\n")
    manager = RuntimeManager(tmp_path, explicit_sd_cli=str(explicit))
    assert manager.resolve() == explicit


def test_resolve_env_var(tmp_path: Path, monkeypatch):
    env_cli = tmp_path / "env-sd-cli"
    _fake_sd_cli(env_cli, "6b3edaa v1", "CPU\n")
    monkeypatch.setenv("MAGE_SD_CLI", str(env_cli))
    manager = RuntimeManager(tmp_path)
    assert manager.resolve() == env_cli


def test_resolve_prebuilt_bin(tmp_path: Path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    prebuilt = bin_dir / "sd-cli"
    _fake_sd_cli(prebuilt, "6b3edaa v1", "CPU\n")
    manager = RuntimeManager(tmp_path)
    assert manager.resolve() == prebuilt


def test_resolve_missing_fails(tmp_path: Path):
    manager = RuntimeManager(tmp_path)
    with pytest.raises(FileNotFoundError):
        manager.resolve()


def test_verify_version_identity(tmp_path: Path):
    cli = tmp_path / "sd-cli"
    _fake_sd_cli(cli, "sd-cli 6b3edaa (master)", "CPU\n")
    manager = RuntimeManager(tmp_path)
    identity = manager.verify(cli, requested_backend="cpu")
    assert identity.pinned_commit == "6b3edaaf32cc19e5bb2d819c788bd557eddc8eba"


def test_verify_wrong_version_fails(tmp_path: Path):
    cli = tmp_path / "sd-cli"
    _fake_sd_cli(cli, "sd-cli deadbeef (master)", "CPU\n")
    manager = RuntimeManager(tmp_path)
    with pytest.raises(ValueError):
        manager.verify(cli, requested_backend="cpu")


def test_verify_cuda_requires_device(tmp_path: Path):
    cli = tmp_path / "sd-cli"
    _fake_sd_cli(cli, "sd-cli 6b3edaa (master)", "CPU\n")
    manager = RuntimeManager(tmp_path)
    with pytest.raises(ValueError):
        manager.verify(cli, requested_backend="cuda0")


def test_verify_cuda_device_present(tmp_path: Path):
    cli = tmp_path / "sd-cli"
    _fake_sd_cli(cli, "sd-cli 6b3edaa (master)", "CUDA0: NVIDIA T4\n")
    manager = RuntimeManager(tmp_path)
    identity = manager.verify(cli, requested_backend="cuda0")
    assert identity.pinned_commit == "6b3edaaf32cc19e5bb2d819c788bd557eddc8eba"
