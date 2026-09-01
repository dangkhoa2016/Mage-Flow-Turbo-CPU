from __future__ import annotations

import json
from pathlib import Path

from mageflow_native.constants import (
    DIT_FILENAME,
    DIT_SHA256,
    QWEN_FILENAME,
    QWEN_SHA256,
    VAE_FILENAME,
    VAE_SHA256,
)
from mageflow_native.models.manifest import sha256_file


class InputResolutionError(RuntimeError):
    pass


def _norm(p: Path) -> str:
    return p.as_posix().lower()


def discover_input(
    root: Path,
    *,
    filename: str,
    required_fragment: str,
    expected_sha256: str,
) -> Path:
    root = Path(root)
    required = required_fragment.lower().strip("/")
    candidates = []
    for p in root.rglob(filename):
        if required in _norm(p):
            candidates.append(p)
    if len(candidates) != 1:
        raise InputResolutionError(
            f"expected exactly one {filename} under *{required_fragment}*, found {len(candidates)}"
        )
    p = candidates[0].resolve()
    digest = sha256_file(p)
    if digest != expected_sha256:
        raise InputResolutionError(f"SHA256 mismatch for {p.name}: {digest}")
    return p


def _relative_or_abs(path: Path, base: Path) -> str:
    try:
        return str(path.resolve().relative_to(base.resolve()))
    except ValueError:
        return str(path.resolve())


def build_kaggle_manifest(
    input_root: Path,
    output: str | Path,
) -> Path:
    input_root = Path(input_root)
    dit = discover_input(
        input_root,
        filename=DIT_FILENAME,
        required_fragment="mage-flow-community-mage-flow-turbo/gguf/q8-0",
        expected_sha256=DIT_SHA256,
    )
    qwen = discover_input(
        input_root,
        filename=QWEN_FILENAME,
        required_fragment="qwen-qwen3-vl-4b-instruct-gguf/gguf/q4-k-m",
        expected_sha256=QWEN_SHA256,
    )
    vae = discover_input(
        input_root,
        filename=VAE_FILENAME,
        required_fragment="mage-flow-community-mage-flow-turbo/pytorch/vae-only",
        expected_sha256=VAE_SHA256,
    )
    manifest = {
        "schema_version": 1,
        "model_family": "Mage-Flow-Turbo",
        "components": {
            "diffusion": {
                "path": _relative_or_abs(dit, input_root),
                "sha256": DIT_SHA256,
                "format": "gguf",
                "quantization": "Q8_0",
            },
            "text_encoder": {
                "path": _relative_or_abs(qwen, input_root),
                "sha256": QWEN_SHA256,
                "format": "gguf",
                "quantization": "Q4_K_M",
            },
            "vae": {
                "path": _relative_or_abs(vae, input_root),
                "sha256": VAE_SHA256,
                "format": "safetensors",
            },
        },
    }
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return output_path
