from pathlib import Path
from mageflow_native.models.manifest import load_manifest, verify_manifest

DIT_SHA = "4c3dafc143ee64121692b6b63563a4f5288bf6183c4870e1d65f1566519ba7f0"


def test_manifest_requires_three_components_and_explicit_sha(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        '{"schema_version":1,"model_family":"Mage-Flow-Turbo","components":{}}'
    )
    try:
        load_manifest(manifest)
    except ValueError as exc:
        assert "diffusion" in str(exc)
    else:
        raise AssertionError("incomplete manifest must fail closed")


def test_manifest_rejects_unknown_schema_version(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        '{"schema_version":99,"model_family":"Mage-Flow-Turbo","components":{}}'
    )
    try:
        load_manifest(manifest)
    except ValueError as exc:
        assert "schema_version" in str(exc)
    else:
        raise AssertionError("unknown schema version must fail closed")


def test_manifest_rejects_extra_components(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    comps = {
        "diffusion": {"path": "a.gguf", "sha256": DIT_SHA, "format": "gguf"},
        "text_encoder": {"path": "b.gguf", "sha256": DIT_SHA, "format": "gguf"},
        "vae": {"path": "c.safetensors", "sha256": DIT_SHA, "format": "safetensors"},
        "extra": {"path": "d.gguf", "sha256": DIT_SHA, "format": "gguf"},
    }
    manifest.write_text(
        json_dumps({"schema_version": 1, "model_family": "Mage-Flow-Turbo", "components": comps})
    )
    try:
        load_manifest(manifest)
    except ValueError as exc:
        assert "extra" in str(exc)
    else:
        raise AssertionError("extra component must fail closed")


def test_verify_manifest_missing_file(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    comps = {
        "diffusion": {"path": "missing.gguf", "sha256": DIT_SHA, "format": "gguf"},
        "text_encoder": {"path": "b.gguf", "sha256": DIT_SHA, "format": "gguf"},
        "vae": {"path": "c.safetensors", "sha256": DIT_SHA, "format": "safetensors"},
    }
    manifest.write_text(
        json_dumps({"schema_version": 1, "model_family": "Mage-Flow-Turbo", "components": comps})
    )
    m = load_manifest(manifest)
    try:
        verify_manifest(m)
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("missing model file must fail closed")


def json_dumps(obj: dict) -> str:
    import json
    return json.dumps(obj)
