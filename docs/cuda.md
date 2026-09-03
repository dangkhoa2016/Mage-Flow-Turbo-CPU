# NVIDIA CUDA

v1.0.0 targets NVIDIA CUDA on explicit `cuda0` (for example a Kaggle T4 / T4x2). Final CUDA qualification is pending; multi-GPU is experimental and not a release gate.

## Prerequisites

- An NVIDIA GPU (release qualification uses `cuda0`)
- CUDA toolkit / `nvcc`
- CMake and a C/C++ toolchain
- the three model files

## Build the pinned CUDA runtime

```bash
python -m pip install -e .
mageflow-native runtime build --backend cuda
```

This uses a deterministic CUDA profile (`-DSD_CUDA=ON`, unrelated GPU backends off). It never silently downgrades to CPU.

## Verify CUDA device

```bash
mageflow-native doctor --manifest configs/mage-flow-turbo-q8-reference.json --backend cuda0
```

Qualification requires `sd-cli --list-devices` to expose a CUDA device resolving to `cuda0`; it fails if CUDA is requested but unavailable.

## Generate on CUDA

```bash
mageflow-native generate --manifest configs/mage-flow-turbo-q8-reference.json \
    --backend cuda0 --prompt "A small red fox" --output output
```

## Low-VRAM placement

The pinned runtime supports separate runtime/parameter placement and per-module assignments. For example on a T4:

```bash
mageflow-native generate --manifest MODEL.json --output output \
    --backend "diffusion=cuda0,te=cpu,vae=cpu" \
    --params-backend "diffusion=cuda0,te=cpu,vae=cpu" \
    --max-vram 4G
```

These syntaxes come from the pinned upstream runtime; mixed/Multi-GPU/Vulkan/Metal/ROCm/SYCL placements are documented upstream but are **not** v1.0.0 qualification targets.

## CUDA acceptance vs CPU

CUDA uses the same canonical request but does not require byte-identical PNG output with the CPU backend (GPU arithmetic may legitimately differ). Acceptance requires:

- valid 512×512 RGB PNG;
- successful `sd-cli` exit;
- exact model hashes;
- explicit CUDA `cuda0` device proof;
- no silent CPU fallback;
- recorded output SHA-256 as the CUDA reference;
- captured wall time and GPU memory telemetry.
