from __future__ import annotations

from pathlib import Path

from mageflow_native.runtime.spec import BackendSpec


def build_sd_cli_argv(
    sd_cli: str | Path,
    *,
    model_paths: dict[str, Path],
    backend_spec: BackendSpec,
    prompt: str,
    seed: int,
    steps: int,
    cfg_scale: float,
    width: int,
    height: int,
    threads: int,
    output_path: str | Path,
    diffusion_fa: bool = True,
) -> list[str]:
    argv = [str(sd_cli)]

    if backend_spec.auto_fit:
        argv += ["--auto-fit"]
    else:
        argv += ["--backend", backend_spec.backend]
        if backend_spec.params_backend:
            argv += ["--params-backend", backend_spec.params_backend]
        if backend_spec.max_vram:
            argv += ["--max-vram", backend_spec.max_vram]
        if backend_spec.split_mode:
            argv += ["--split-mode", backend_spec.split_mode]

    argv += [
        "--diffusion-model", str(model_paths["diffusion"]),
        "--llm", str(model_paths["text_encoder"]),
        "--vae", str(model_paths["vae"]),
        "-p", prompt,
        "--cfg-scale", f"{cfg_scale:.1f}",
        "--steps", str(steps),
        "-W", str(width),
        "-H", str(height),
        "-s", str(seed),
        "-t", str(threads),
        "--output", str(output_path),
    ]

    if diffusion_fa:
        argv.append("--diffusion-fa")

    return argv
