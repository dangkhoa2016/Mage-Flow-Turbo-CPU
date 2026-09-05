# Mage-Flow-Turbo-Native-Inference

[![CI](https://github.com/dangkhoa2016/Mage-Flow-Turbo-Native-Inference/actions/workflows/ci.yml/badge.svg)](https://github.com/dangkhoa2016/Mage-Flow-Turbo-Native-Inference/actions/workflows/ci.yml)
[![Native Runtime](https://github.com/dangkhoa2016/Mage-Flow-Turbo-Native-Inference/actions/workflows/native-runtime.yml/badge.svg)](https://github.com/dangkhoa2016/Mage-Flow-Turbo-Native-Inference/actions/workflows/native-runtime.yml)
[![Release](https://img.shields.io/github/v/release/dangkhoa2016/Mage-Flow-Turbo-Native-Inference)](https://github.com/dangkhoa2016/Mage-Flow-Turbo-Native-Inference/releases/tag/v1.0.0)
[![License](https://img.shields.io/github/license/dangkhoa2016/Mage-Flow-Turbo-Native-Inference)](LICENSE)

> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](README.vi.md)

A **portable native inference and deployment stack for Mage-Flow-Turbo**. This repository does not define a new model and does not train or fine-tune model weights. Python provides configuration, validation, CLI/REST orchestration, lifecycle control and evidence collection; model inference itself is executed by the native `stable-diffusion.cpp` `sd-cli` runtime.

```text
manifest → SHA-256 verification → pinned sd-cli runtime
        → Mage-Flow-Turbo DiT Q8_0
        → Qwen3-VL-4B text encoder Q4_K_M
        → dedicated VAE
        → Linux CPU or NVIDIA CUDA cuda0
        → PNG artifact + structured evidence
```

## Exact reference stack

| Role | Exact artifact | Format / quantization |
|---|---|---|
| Diffusion model | `Mage-Flow-Turbo-DiT-Q8_0.gguf` | GGUF Q8_0 |
| Text encoder | `Qwen3VL-4B-Instruct-Q4_K_M.gguf` | GGUF Q4_K_M |
| VAE | `diffusion_pytorch_model.safetensors` | SafeTensors |
| Native runtime | `stable-diffusion.cpp` `sd-cli` | pinned commit `6b3edaaf32cc19e5bb2d819c788bd557eddc8eba` |

Frozen SHA-256 identities are enforced before real inference. The repository contains no model weights.

## v1.0.0 qualification scope

The first public release is qualified against one exact Git source head and one frozen model/runtime contract. Release targets are:

| Environment | Backend | Release scope |
|---|---|---|
| Linux x86-64 | CPU | qualified release target |
| Linux + NVIDIA GPU | CUDA `cuda0` | qualified release target |
| Kaggle CPU notebook | CPU adapter | qualified integration target |
| Kaggle T4/T4x2 notebook | CUDA adapter `cuda0` on physical GPU 0 | qualified integration target |

Multi-GPU inference, Vulkan, Metal, ROCm, SYCL, Windows and other backends are not v1.0.0 release qualification targets.

Final exact-head qualification evidence, measured wall times, RAM/VRAM telemetry, runtime binary hashes, acceptance PNG hashes, executed notebooks, release provenance and SHA-256 checksums are published with the GitHub Release rather than embedded as mutable source-tree state.

## Why native inference?

The diffusion step, text conditioning and VAE decoding are executed by `sd-cli`; there is no PyTorch/Transformers inference loop in the project. Python validates model identity, builds explicit subprocess arguments with `shell=False`, monitors the native process and records evidence.

## Verify the model stack

Model files are user-supplied or mounted. Loading uses a JSON model manifest and fails closed when a required component is missing, ambiguous or hash-mismatched.

```bash
mageflow-native verify --manifest configs/mage-flow-turbo-q8-reference.json
```

## Linux CPU quick start

Prerequisites: Linux, Python 3.10+, CMake and a C/C++ toolchain.

```bash
python -m pip install -e .
mageflow-native runtime build --backend cpu
mageflow-native doctor --manifest configs/mage-flow-turbo-q8-reference.json
mageflow-native verify --manifest configs/mage-flow-turbo-q8-reference.json
mageflow-native generate \
  --manifest configs/mage-flow-turbo-q8-reference.json \
  --prompt "A small red fox sitting in a quiet green forest" \
  --output output
```

## NVIDIA CUDA quick start

Prerequisites: an NVIDIA GPU, CUDA toolkit, CMake and a C/C++ toolchain.

```bash
python -m pip install -e .
mageflow-native runtime build --backend cuda
mageflow-native doctor \
  --manifest configs/mage-flow-turbo-q8-reference.json \
  --backend cuda0
mageflow-native generate \
  --manifest configs/mage-flow-turbo-q8-reference.json \
  --backend cuda0 \
  --prompt "A small red fox" \
  --output output
```

Release qualification uses explicit deterministic placement (`cpu` or `cuda0`), never `auto` or `--auto-fit`.

## CLI

```text
mageflow-native doctor
mageflow-native verify
mageflow-native generate
mageflow-native serve
mageflow-native runtime build --backend cpu|cuda
```

## REST API

The reference service binds to `127.0.0.1` by default.

```text
GET  /healthz
GET  /readyz
GET  /v1/info
POST /v1/images/generate
GET  /v1/artifacts/<png>
```

Public exposure, when desired, is a separate authenticated gateway concern and is outside release qualification.

## Kaggle integration

Kaggle is an adapter/reference environment rather than a hard dependency of the core. Kaggle-specific discovery lives under `integrations/kaggle/`; it maps mounted inputs into the generic manifest/runtime flow. See [docs/kaggle.md](docs/kaggle.md) and [notebooks/kaggle-production-demo.ipynb](notebooks/kaggle-production-demo.ipynb).

## Reproducibility and evidence

Qualification records exact Git head, runtime provenance, model hashes, backend, prompt, seed, steps, CFG, thread count, resolution, exact argv, stdout/stderr, exit code, wall time, peak memory telemetry and PNG identity. Evidence archives are sanitized and clean-room verifiable.

Canonical release request:

```text
prompt  = A small red fox sitting in a quiet green forest, natural light, detailed photography.
size    = 512x512
seed    = 42
steps   = 4
CFG     = 1.0
threads = 4
```

CPU and CUDA outputs may legitimately differ byte-for-byte across numerical backends.

## Documentation

- [Architecture](docs/architecture.md)
- [Model stack](docs/model-stack.md)
- [Local Linux](docs/local-linux.md)
- [CUDA](docs/cuda.md)
- [Kaggle](docs/kaggle.md)
- [REST API](docs/REST-API.md)
- [Testing](docs/TESTING.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Contributing](.github/CONTRIBUTING.md)
- [Security policy](.github/SECURITY.md)

## License

MIT License. Copyright © 2026 Đăng Khoa <i.am@dangkhoa.dev>.
