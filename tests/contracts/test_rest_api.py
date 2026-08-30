import json
import threading
from pathlib import Path

import pytest

from mageflow_native.models.manifest import ModelManifest, ModelComponent
from mageflow_native.service.http import build_server, validate_generation_payload

DIT_SHA = "4c3dafc143ee64121692b6b63563a4f5288bf6183c4870e1d65f1566519ba7f0"


def _make_manifest(tmp_path: Path) -> ModelManifest:
    return ModelManifest(
        schema_version=1,
        model_family="Mage-Flow-Turbo",
        diffusion=ModelComponent(tmp_path / "dit.gguf", DIT_SHA, "gguf", "Q8_0"),
        text_encoder=ModelComponent(tmp_path / "qwen.gguf", DIT_SHA, "gguf", "Q4_K_M"),
        vae=ModelComponent(tmp_path / "vae.safetensors", DIT_SHA, "safetensors"),
    )


def test_validate_generation_payload_ok():
    data = validate_generation_payload(
        {"prompt": "fox", "seed": 42, "client_request_id": "abc-123", "backend": "cpu"}
    )
    assert data["prompt"] == "fox"
    assert data["seed"] == 42


def test_validate_generation_payload_requires_prompt():
    with pytest.raises(ValueError):
        validate_generation_payload({})


def test_validate_generation_payload_rejects_unknown_fields():
    with pytest.raises(ValueError):
        validate_generation_payload({"prompt": "x", "bogus": 1})


def test_validate_generation_payload_seed_range():
    with pytest.raises(ValueError):
        validate_generation_payload({"prompt": "x", "seed": 2**32})
    with pytest.raises(ValueError):
        validate_generation_payload({"prompt": "x", "seed": -1})


def test_validate_generation_payload_invalid_request_id():
    with pytest.raises(ValueError):
        validate_generation_payload({"prompt": "x", "client_request_id": "a b"})


def test_server_fake_endpoints(tmp_path: Path):
    config = {
        "host": "127.0.0.1",
        "port": 0,
        "sd_cli": "fake",
        "manifest": _make_manifest(tmp_path),
        "output_dir": str(tmp_path / "out"),
        "runs_dir": str(tmp_path / "runs"),
        "timeout_seconds": 60,
        "backend": "cpu",
    }
    server = build_server(config, fake=True)
    port = server.server_address[1]
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    import urllib.request

    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/healthz") as resp:
            assert resp.status == 200
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/readyz") as resp:
            assert resp.status == 200
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/v1/info") as resp:
            assert resp.status == 200
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/v1/images/generate",
            data=json.dumps({"prompt": "fox", "backend": "cpu"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read().decode())
            assert body["status"] == "succeeded"
            assert body["width"] == 512
            artifact_url = body["artifact_url"]
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}{artifact_url}"
        ) as resp:
            assert resp.status == 200
            assert resp.read().startswith(b"\x89PNG")
    finally:
        server.shutdown()
        server.server_close()
