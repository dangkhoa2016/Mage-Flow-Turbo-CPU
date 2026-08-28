from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from mageflow_native.constants import SDCPP_COMMIT, SDCPP_SHORT
from mageflow_native.runtime.spec import RuntimeBuildBackend


@dataclass(frozen=True)
class RuntimeIdentity:
    path: str
    version_output: str
    devices_output: str
    pinned_commit: str


class RuntimeManager:
    def __init__(
        self,
        runtime_root: Path,
        *,
        explicit_sd_cli: str | None = None,
    ) -> None:
        self.runtime_root = runtime_root
        self.explicit_sd_cli = explicit_sd_cli

    def resolve(self) -> Path:
        if self.explicit_sd_cli:
            p = Path(self.explicit_sd_cli)
            if p.is_file() and os.access(p, os.X_OK):
                return p
        env_cli = os.environ.get("MAGE_SD_CLI")
        if env_cli:
            p = Path(env_cli)
            if p.is_file() and os.access(p, os.X_OK):
                return p
        prebuilt = self.runtime_root / "bin" / "sd-cli"
        if prebuilt.is_file() and os.access(prebuilt, os.X_OK):
            return prebuilt
        build_path = self.runtime_root / "build" / "bin" / "sd-cli"
        if build_path.is_file() and os.access(build_path, os.X_OK):
            return build_path
        raise FileNotFoundError(
            "sd-cli not found; run 'mageflow-native runtime build' or set MAGE_SD_CLI"
        )

    def build(self, build_backend: RuntimeBuildBackend) -> Path:
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        src_dir = self.runtime_root / "src"
        build_dir = self.runtime_root / "build"
        if not src_dir.exists():
            subprocess.run(
                [
                    "git", "clone", "--depth", "1",
                    "--branch", "master",
                    "https://github.com/leejet/stable-diffusion.cpp.git",
                    str(src_dir),
                ],
                check=True,
                capture_output=True,
            )
        subprocess.run(
            ["git", "fetch", "--depth", "1", "origin", SDCPP_COMMIT],
            cwd=str(src_dir),
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "checkout", SDCPP_COMMIT],
            cwd=str(src_dir),
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "submodule", "update", "--init", "--recursive"],
            cwd=str(src_dir),
            check=True,
            capture_output=True,
        )
        build_dir.mkdir(parents=True, exist_ok=True)
        cmake_flags = build_backend.cmake_flags
        subprocess.run(
            ["cmake", str(src_dir), "-B", str(build_dir)] + cmake_flags,
            check=True,
            capture_output=True,
        )
        nproc = os.cpu_count() or 1
        subprocess.run(
            ["cmake", "--build", str(build_dir), "-j", str(nproc), "--target", "sd-cli"],
            check=True,
            capture_output=True,
        )
        sd_cli = build_dir / "bin" / "sd-cli"
        if not sd_cli.exists():
            for candidate in build_dir.rglob("sd-cli"):
                if candidate.is_file():
                    sd_cli = candidate
                    break
        if not sd_cli.exists():
            raise FileNotFoundError("sd-cli not built successfully")
        return sd_cli

    def verify(self, sd_cli_path: Path, requested_backend: str) -> RuntimeIdentity:
        version_result = subprocess.run(
            [str(sd_cli_path), "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        version_output = version_result.stdout.strip()
        if SDCPP_SHORT not in version_output:
            raise ValueError(
                f"sd-cli version {version_output!r} does not contain pinned commit {SDCPP_SHORT}"
            )
        devices_result = subprocess.run(
            [str(sd_cli_path), "--list-devices"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        devices_output = devices_result.stdout.strip()
        if requested_backend == "cpu":
            if "cuda" in devices_output.lower() and "gpu" in devices_output.lower():
                pass
        elif requested_backend == "cuda0":
            if "cuda" not in devices_output.lower():
                raise ValueError(
                    f"CUDA requested but no CUDA device found: {devices_output}"
                )
        return RuntimeIdentity(
            path=str(sd_cli_path.resolve()),
            version_output=version_output,
            devices_output=devices_output,
            pinned_commit=SDCPP_COMMIT,
        )
