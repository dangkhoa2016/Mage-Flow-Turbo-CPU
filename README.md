# Mage-Flow-Turbo-Native-Inference

[![CI](https://github.com/dangkhoa2016/Mage-Flow-Turbo-Native-Inference/actions/workflows/ci.yml/badge.svg)](https://github.com/dangkhoa2016/Mage-Flow-Turbo-Native-Inference/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/dangkhoa2016/Mage-Flow-Turbo-Native-Inference)](LICENSE)
![Linux CPU](https://img.shields.io/badge/Linux%20CPU-qualification%20pending-yellow)
![NVIDIA CUDA](https://img.shields.io/badge/NVIDIA%20CUDA-qualification%20pending-yellow)
![Kaggle](https://img.shields.io/badge/Kaggle-adapter%2Freference-20BEFF?logo=kaggle&logoColor=white)

> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](README.vi.md)

A **portable native inference and deployment stack for Mage-Flow-Turbo**. This is not a new model and it does not train or fine-tune anything. Python provides configuration, validation, CLI/REST orchestration, lifecycle control and evidence collection; the actual model inference is executed by the native `stable-diffusion.cpp` `sd-cli` runtime.

**What actually runs:**

```text
manifest → SHA-256 verification → runtime manager (sd-cli)
        → Mage-Flow-Turbo DiT (Q8_0) with Qwen3-VL-4B text encoder and dedicated VAE
        → Linux CPU or NVIDIA CUDA (cuda0)
        → PNG artifact
```

## Exact model stack

| Role | Exact artifact | Format / quantization | Reference source |
|---|---|---|---|
| Diffusion model | `Mage-Flow-Turbo-DiT-Q8_0.gguf` | GGUF Q8_0 | `mage-flow-community-mage-flow-turbo/gguf/q8-0` |
| Text encoder / LLM | `Qwen3VL-4B-Instruct-Q4_K_M.gguf` | GGUF Q4_K_M | `qwen-qwen3-vl-4b-instruct-gguf/gguf/q4-k-m` |
| VAE | `diffusion_pytorch_model.safetensors` | SafeTensors | `mage-flow-community-mage-flow-turbo/pytorch/vae-only` |
| Native engine | `stable-diffusion.cpp` `sd-cli` | C/C++ native | pinned commit `6b3edaaf32cc19e5bb2d819c788bd557eddc8eba` |

All three model components are required. Frozen SHA-256 identities and the pinned runtime are verified before any real inference. **Python is orchestration, not the denoising engine** — there is no PyTorch/Transformers inference loop.

## Why this project exists

The community value is a reproducible answer to a deployment problem:

- which Mage-Flow-Turbo components must be loaded;
- which quantizations are known-good;
- how the DiT, text encoder and VAE wire into `stable-diffusion.cpp`;
- how to verify exact model identities before inference;
- how to run the same stack on CPU or NVIDIA CUDA without a PyTorch inference loop;
- how to expose it through a local CLI and REST API;
- how to collect reproducible runtime/evidence data;
- how to adapt the same generic core to Kaggle without embedding Kaggle assumptions into the core.

## Platform support & qualification status

| Environment | Backend | v1.0.0 status |
|---|---|---:|
| Linux x86-64 | CPU | Qualification pending |
| Linux + NVIDIA GPU | CUDA (`cuda0`) | Qualification pending |
| Kaggle CPU notebook | CPU adapter | Qualification pending |
| Kaggle T4/T4x2 notebook | CUDA adapter (`cuda0`) | Qualification pending |
| CUDA multi-GPU | `cuda0&cuda1` | Experimental / not a release gate |
| Vulkan / Metal / ROCm / SYCL / Windows | GPU | Planned / not a release target for v1.0.0 |

## Why no PyTorch?

The diffusion step, text conditioning and VAE decoding are all executed by the native `sd-cli` runtime. Python only validates configuration and models, builds the explicit subprocess argv (`shell=False`), monitors the process, and collects evidence.

## Model loading and SHA verification

Model files are **user-supplied or mounted**; the repository does not commit model weights. Loading uses a JSON model manifest:

```bash
mageflow-native verify --manifest configs/mage-flow-turbo-q8-reference.json
```

Every canonical component is SHA-256 verified before a real inference service starts. A missing or ambiguous component **fails closed**. Explicit paths override discovery.

## Local Linux quick start

Prerequisites: Linux, Python 3.10+, CMake, a C/C++ toolchain.

```bash
python -m pip install -e .
mageflow-native runtime build --backend cpu      # build the pinned CPU sd-cli
mageflow-native doctor --manifest configs/mage-flow-turbo-q8-reference.json
mageflow-native verify --manifest configs/mage-flow-turbo-q8-reference.json
mageflow-native generate \
    --manifest configs/mage-flow-turbo-q8-reference.json \
    --prompt "A small red fox sitting in a quiet green forest" --output output
```

Provide the three model files at the manifest paths (or set `MAGE_MODEL_ROOT`), or point `--manifest`/`--model-root` at your own layout.

## NVIDIA CUDA quick start

Prerequisites: an NVIDIA GPU, CUDA toolkit, CMake, a C/C++ toolchain.

```bash
python -m pip install -e .
mageflow-native runtime build --backend cuda      # deterministic CUDA build of the pinned source
mageflow-native doctor --manifest configs/mage-flow-turbo-q8-reference.json --backend cuda0
mageflow-native generate --manifest configs/mage-flow-turbo-q8-reference.json \
    --backend cuda0 --prompt "A small red fox" --output output
```

Qualification uses explicit deterministic placement (`cpu` or `cuda0`), never `auto` or `--auto-fit`.

## Backend placement / low-VRAM examples

The pinned runtime supports separate runtime and parameter placement as well as per-module assignments. For example on a low-VRAM T4:

```bash
mageflow-native generate --manifest MODEL.json --output output \
    --backend "diffusion=cuda0,te=cpu,vae=cpu" \
    --params-backend "diffusion=cuda0,te=cpu,vae=cpu" \
    --max-vram 4G
```

Multi-GPU, Vulkan, Metal, ROCm and SYCL are documented upstream features but are **not v1.0.0 qualification targets**.

## Kaggle integration

Kaggle is an **adapter/reference environment**, not a required runtime platform. Final live CPU/CUDA qualification for v1.0.0 is pending. Kaggle-specific behavior lives under `integrations/kaggle/` and only discovers mounted inputs and generates a generic manifest; the same generic core then runs on CPU or CUDA. See [docs/kaggle.md](docs/kaggle.md) and [notebooks/kaggle-production-demo.ipynb](notebooks/kaggle-production-demo.ipynb).

## CLI

```text
mageflow-native doctor                       show OS/arch, runtime, devices, backend, manifest
mageflow-native verify                       verify runtime and model identities (no inference)
mageflow-native generate [GENERATION]        one local generation
mageflow-native serve                        start loopback REST service
mageflow-native runtime build --backend cpu|cuda
```

## REST API

The loopback service binds to `127.0.0.1` by default.

```text
GET  /healthz
GET  /readyz
GET  /v1/info
POST /v1/images/generate
GET  /v1/artifacts/<png>
```

See [docs/REST-API.md](docs/REST-API.md). Public exposure, if used, is a separate authenticated gateway and is not part of qualification.

## Reproducibility / evidence

The qualification harnesses record backend spec, runtime identity, model hashes, prompt/seed/steps/CFG/threads/resolution, exit code, wall time, peak RAM and (CUDA) GPU telemetry, PNG dimensions/mode/size/SHA, and the exact source Git head. Evidence is packaged sanitized. See [docs/TESTING.md](docs/TESTING.md) and [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

## Canonical qualification request

The canonical qualification request produces one 512×512 PNG with seed 42, 4 steps, CFG 1.0, 4 threads and the canonical fox prompt. Final CPU and CUDA reference SHA-256 values are recorded only after the exact published source head passes the corresponding external qualification gate. CUDA output may legitimately differ in bytes from CPU output.

## Limitations

- No automatic model downloading in the core; users supply files.
- Windows, macOS, AMD ROCm, Metal, Vulkan and Intel SYCL are **not** v1.0.0 qualification targets.
- No training, fine-tuning or model conversion.
- Only the frozen Q8_0 + Q4_K_M reference stack is in v1.0.0 qualification scope.

## Documentation and contributing

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
