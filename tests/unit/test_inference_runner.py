import json
import struct
import subprocess
import sys
import textwrap
import zlib
from pathlib import Path

from mageflow_native.models.manifest import ModelManifest, ModelComponent
from mageflow_native.runtime.spec import BackendSpec

DIT_SHA = "4c3dafc143ee64121692b6b63563a4f5288bf6183c4870e1d65f1566519ba7f0"
QWEN_SHA = "66358cb18bb6b3b1b6675aa412c7a88ef01d228f481184d13668e5201c730a0a"
VAE_SHA = "34e076dc1e8a15321e1e07be5111d59cf16dd10b804b7c7e20b4de29013427e0"


def _fake_sd_cli(path: Path) -> None:
    script = textwrap.dedent(
        '''\
        #!/usr/bin/env python3
        import argparse
        p = argparse.ArgumentParser()
        p.add_argument("--output")
        args, _ = p.parse_known_args()
        if args.output:
            import struct, zlib
            w = h = 512
            sig = b"\\x89PNG\\r\\n\\x1a\\n"
            def chunk(kind, data):
                return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
            row = bytes([32, 96, 48]) * w
            raw = b"".join(b"\\x00" + row for _ in range(h))
            data = sig + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b"")
            with open(args.output, "wb") as f:
                f.write(data)
        print("fake-ok")
        '''
    )
    path.write_text(script)
    path.chmod(0o755)


def _make_manifest(tmp_path: Path) -> ModelManifest:
    return ModelManifest(
        schema_version=1,
        model_family="Mage-Flow-Turbo",
        diffusion=ModelComponent(tmp_path / "dit.gguf", DIT_SHA, "gguf", "Q8_0"),
        text_encoder=ModelComponent(tmp_path / "qwen.gguf", QWEN_SHA, "gguf", "Q4_K_M"),
        vae=ModelComponent(tmp_path / "vae.safetensors", VAE_SHA, "safetensors"),
    )


def test_run_generation_fake(tmp_path: Path):
    from mageflow_native.inference.runner import run_generation
    manifest = _make_manifest(tmp_path)
    out = tmp_path / "out"
    runs = tmp_path / "runs"
    result = run_generation(
        "fake-cli",
        manifest,
        BackendSpec(backend="cpu", params_backend="cpu"),
        prompt="fox",
        seed=42,
        output_dir=out,
        runs_dir=runs,
        client_request_id="t1",
        timeout_seconds=60,
        fake=True,
    )
    assert result.exit_code == 0
    assert result.artifact.width == 512
    assert result.artifact.height == 512
    assert (out / "t1.png").is_file()
    assert (runs / "t1" / "request.json").is_file()
    assert (runs / "t1" / "result.json").is_file()
    assert (runs / "t1" / "telemetry.json").is_file()


def test_run_generation_real_fake_cli(tmp_path: Path):
    from mageflow_native.inference.runner import run_generation
    fake_cli = tmp_path / "fake-cli"
    _fake_sd_cli(fake_cli)
    manifest = _make_manifest(tmp_path)
    out = tmp_path / "out"
    runs = tmp_path / "runs"
    result = run_generation(
        fake_cli,
        manifest,
        BackendSpec(backend="cpu", params_backend="cpu"),
        prompt="fox",
        seed=42,
        output_dir=out,
        runs_dir=runs,
        client_request_id="t2",
        timeout_seconds=60,
        fake=False,
    )
    assert result.exit_code == 0
    assert result.artifact.width == 512
    assert (out / "t2.png").is_file()
    argv = json.loads((runs / "t2" / "argv.json").read_text())
    assert argv[0] == str(fake_cli)
    assert "--backend" in argv
