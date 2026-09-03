# Architecture

Mage-Flow-Turbo-Native-Inference is a portable native inference and deployment stack for Mage-Flow-Turbo. It is not a model and does not train or fine-tune anything.

## High-level flow

```text
                 Text prompt
                     │
                     ▼
        Qwen3-VL-4B-Instruct (Q4_K_M GGUF)
                     │  conditioning
                     ▼
        Mage-Flow-Turbo DiT (Q8_0 GGUF)
                     │  latents
                     ▼
        Dedicated Mage-Flow VAE (SafeTensors)
                     │
                     ▼
        stable-diffusion.cpp / sd-cli  (native)
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
     Linux CPU            NVIDIA CUDA
 (qualification pending)  (cuda0, qualification pending)
          │                     │
          └──────────┬──────────┘
                     ▼
                 PNG artifact
```

## Python is orchestration, not inference

Python provides:

- configuration and model manifest validation;
- SHA-256 verification of every canonical component;
- CLI (`doctor`, `verify`, `generate`, `serve`, `runtime build`);
- loopback REST service;
- lifecycle control and evidence collection.

The actual denoising, conditioning and VAE decoding are executed by the native `sd-cli` runtime. Python always invokes `sd-cli` with `shell=False` and explicit argv; no shell interpolation of backend specs, paths, prompts or request IDs.

## Portability boundary

The **generic core** (`mageflow_native/`) contains no hard-coded `/kaggle/input` or `/kaggle/working` paths. It uses normal Linux filesystem semantics:

- runtime/cache root: `${MAGE_RUNTIME_ROOT}` or `${XDG_CACHE_HOME:-~/.cache}/mage-flow-turbo-native`
- model manifest: `--manifest` / `MAGE_MODEL_MANIFEST`
- model root: `--model-root` / `MAGE_MODEL_ROOT`
- runtime binary: `--sd-cli` / `MAGE_SD_CLI`, prebuilt artifact, or pinned source build

Kaggle-specific behavior lives under `integrations/kaggle/` and is an adapter over the same generic core.

## Runtime manager resolution order

1. explicit `MAGE_SD_CLI` / `--sd-cli` path
2. configured verified prebuilt runtime artifact
3. source build from pinned `stable-diffusion.cpp` commit `6b3edaaf32cc19e5bb2d819c788bd557eddc8eba`

## Backend configuration

- Simple: `auto`, `cpu`, `cuda0`
- Advanced: validated assignment strings such as `diffusion=cuda0,te=cpu,vae=cpu`, plus `max_vram`, `split_mode`, `auto_fit`
- `auto_fit` is mutually exclusive with explicit assignments
- Qualification always uses explicit deterministic placement (`cpu` or `cuda0`), never `auto`/`auto-fit`

## Security

- `shell=False` for all subprocesses
- Model and runtime hashes verified before real inference
- REST backend binds loopback by default
- Public exposure is a separate authenticated gateway
- Evidence collectors sanitize secrets and exclude raw argv / credential-bearing environment values
