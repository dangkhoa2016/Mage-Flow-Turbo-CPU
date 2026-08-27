from __future__ import annotations

import re
from dataclasses import dataclass

_SIMPLE_BACKENDS = frozenset({"auto", "cpu", "cuda0"})
_ADVANCED_PATTERN = re.compile(r"^[A-Za-z0-9_*=,&.\-]+$")


def _validate_advanced_spec(value: str, field: str) -> None:
    if not value:
        return
    if not _ADVANCED_PATTERN.match(value):
        raise ValueError(
            f"invalid {field} {value!r}: contains disallowed characters"
        )


def _validate_backend_value(value: str) -> None:
    if value in _SIMPLE_BACKENDS:
        return
    _validate_advanced_spec(value, "backend")


def _validate_params_backend_value(value: str) -> None:
    if value in _SIMPLE_BACKENDS:
        return
    _validate_advanced_spec(value, "params_backend")


@dataclass(frozen=True)
class BackendSpec:
    backend: str = "auto"
    params_backend: str | None = None
    max_vram: str | None = None
    split_mode: str | None = None
    auto_fit: bool = False

    def __post_init__(self) -> None:
        _validate_backend_value(self.backend)
        if self.params_backend is not None:
            _validate_params_backend_value(self.params_backend)
        if self.auto_fit and (self.backend != "auto" or self.params_backend is not None):
            raise ValueError(
                "auto_fit is mutually exclusive with explicit backend/params assignments"
            )
        if self.max_vram is not None:
            _validate_advanced_spec(self.max_vram, "max_vram")
        if self.split_mode is not None:
            _validate_advanced_spec(self.split_mode, "split_mode")


@dataclass(frozen=True)
class RuntimeBuildBackend:
    backend: str

    def __post_init__(self) -> None:
        if self.backend not in ("cpu", "cuda"):
            raise ValueError(f"build backend must be cpu or cuda, got {self.backend!r}")

    @property
    def cmake_flags(self) -> list[str]:
        base = [
            "-DCMAKE_BUILD_TYPE=Release",
            "-DSD_HIPBLAS=OFF",
            "-DSD_METAL=OFF",
            "-DSD_VULKAN=OFF",
            "-DSD_OPENCL=OFF",
            "-DSD_SYCL=OFF",
            "-DSD_MUSA=OFF",
            "-DSD_RPC=OFF",
            "-DGGML_NATIVE=ON",
        ]
        if self.backend == "cuda":
            return base + [
                "-DSD_CUDA=ON",
                "-DGGML_CUDA_NO_VMM=ON",
            ]
        return base + ["-DSD_CUDA=OFF"]
