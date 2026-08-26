from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from mageflow_native.constants import (
    DIT_SHA256,
    QWEN_SHA256,
    VAE_SHA256,
)

_REQUIRED_COMPONENTS = ("diffusion", "text_encoder", "vae")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def sha256_file(path: str | Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass(frozen=True)
class ModelComponent:
    path: Path
    sha256: str
    format: str
    quantization: str | None = None


@dataclass(frozen=True)
class ModelManifest:
    schema_version: int
    model_family: str
    diffusion: ModelComponent
    text_encoder: ModelComponent
    vae: ModelComponent


def _validate_hex64(value: str, field: str) -> None:
    if not isinstance(value, str) or not _HEX64.match(value):
        raise ValueError(f"malformed 64-hex SHA-256 in {field}: {value!r}")


def _validate_component(name: str, raw: dict, base: Path, model_root: Path | None) -> ModelComponent:
    if not isinstance(raw, dict):
        raise ValueError(f"component {name!r} must be a JSON object")
    path_str = raw.get("path")
    if not isinstance(path_str, str) or not path_str.strip():
        raise ValueError(f"component {name!r} has empty path")
    sha = raw.get("sha256", "")
    _validate_hex64(sha, f"{name}.sha256")
    fmt = raw.get("format", "")
    if not isinstance(fmt, str) or not fmt:
        raise ValueError(f"component {name!r} has empty format")
    quant = raw.get("quantization")
    if quant is not None and not isinstance(quant, str):
        raise ValueError(f"component {name!r} has invalid quantization")
    p = Path(path_str)
    if not p.is_absolute():
        p = (model_root if model_root else base) / p
    return ModelComponent(path=p, sha256=sha, format=fmt, quantization=quant)


def load_manifest(
    path: str | Path,
    *,
    model_root: str | Path | None = None,
) -> ModelManifest:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("manifest must be a JSON object")
    sv = data.get("schema_version")
    if sv != 1:
        raise ValueError(f"unsupported schema_version: {sv}")
    mf = data.get("model_family", "")
    if mf != "Mage-Flow-Turbo":
        raise ValueError(f"unexpected model_family: {mf!r}")
    comps = data.get("components")
    if not isinstance(comps, dict):
        raise ValueError("manifest missing components")
    keys = set(comps.keys())
    missing = set(_REQUIRED_COMPONENTS) - keys
    if missing:
        raise ValueError(f"manifest missing required components: {sorted(missing)}")
    extra = keys - set(_REQUIRED_COMPONENTS)
    if extra:
        raise ValueError(f"manifest has unexpected components: {sorted(extra)}")
    mr = Path(model_root) if model_root else None
    base = path.parent
    diffusion = _validate_component("diffusion", comps["diffusion"], base, mr)
    text_encoder = _validate_component("text_encoder", comps["text_encoder"], base, mr)
    vae = _validate_component("vae", comps["vae"], base, mr)
    return ModelManifest(
        schema_version=sv,
        model_family=mf,
        diffusion=diffusion,
        text_encoder=text_encoder,
        vae=vae,
    )


def verify_manifest(manifest: ModelManifest) -> dict[str, Path]:
    verified: dict[str, Path] = {}
    for name, component in {
        "diffusion": manifest.diffusion,
        "text_encoder": manifest.text_encoder,
        "vae": manifest.vae,
    }.items():
        if not component.path.is_file():
            raise FileNotFoundError(component.path)
        digest = sha256_file(component.path)
        if digest != component.sha256:
            raise ValueError(f"SHA256 mismatch for {name}: {digest}")
        verified[name] = component.path.resolve()
    return verified
