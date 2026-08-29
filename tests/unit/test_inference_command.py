from pathlib import Path

from mageflow_native.inference.command import build_sd_cli_argv
from mageflow_native.runtime.spec import BackendSpec

SD_CLI = "/usr/local/bin/sd-cli"
MODELS = {
    "diffusion": Path("/models/dit.gguf"),
    "text_encoder": Path("/models/qwen.gguf"),
    "vae": Path("/models/vae.safetensors"),
}


def test_cpu_qualification_argv():
    backend = BackendSpec(backend="cpu", params_backend="cpu")
    argv = build_sd_cli_argv(
        SD_CLI,
        model_paths=MODELS,
        backend_spec=backend,
        prompt="fox",
        seed=42,
        steps=4,
        cfg_scale=1.0,
        width=512,
        height=512,
        threads=4,
        output_path="/out/x.png",
    )
    assert argv[:5] == [SD_CLI, "--backend", "cpu", "--params-backend", "cpu"]
    assert "--diffusion-model" in argv
    assert "--auto-fit" not in argv


def test_cuda_qualification_argv():
    backend = BackendSpec(backend="cuda0")
    argv = build_sd_cli_argv(
        SD_CLI,
        model_paths=MODELS,
        backend_spec=backend,
        prompt="fox",
        seed=42,
        steps=4,
        cfg_scale=1.0,
        width=512,
        height=512,
        threads=4,
        output_path="/out/x.png",
    )
    idx = argv.index("--backend")
    assert ["--backend", "cuda0"] == argv[idx:idx + 2]
    assert "--params-backend" not in argv


def test_mixed_placement_single_argv_value():
    backend = BackendSpec(backend="diffusion=cuda0,te=cpu,vae=cpu")
    argv = build_sd_cli_argv(
        SD_CLI,
        model_paths=MODELS,
        backend_spec=backend,
        prompt="fox",
        seed=42,
        steps=4,
        cfg_scale=1.0,
        width=512,
        height=512,
        threads=4,
        output_path="/out/x.png",
    )
    idx = argv.index("--backend")
    assert argv[idx + 1] == "diffusion=cuda0,te=cpu,vae=cpu"
    assert argv.count("diffusion=cuda0,te=cpu,vae=cpu") == 1


def test_auto_fit_no_explicit_backend():
    backend = BackendSpec(backend="auto", auto_fit=True)
    argv = build_sd_cli_argv(
        SD_CLI,
        model_paths=MODELS,
        backend_spec=backend,
        prompt="fox",
        seed=42,
        steps=4,
        cfg_scale=1.0,
        width=512,
        height=512,
        threads=4,
        output_path="/out/x.png",
    )
    assert "--auto-fit" in argv
    assert "--backend" not in argv
