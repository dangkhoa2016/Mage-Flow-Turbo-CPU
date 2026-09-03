# Local Linux (CPU)

The generic core runs on a normal Linux machine without any Kaggle conventions.

## Prerequisites

- Linux x86-64
- Python 3.10+
- CMake and a C/C++ toolchain
- the three model files (DiT Q8_0, Qwen Q4_K_M, VAE)

## Install

```bash
python -m pip install -e .
```

## Build the pinned CPU runtime

```bash
mageflow-native runtime build --backend cpu
```

This clones the pinned `stable-diffusion.cpp` commit, configures a deterministic CPU-only build, and builds `sd-cli`.

## Point the manifest at your models

Use `--manifest` with an explicit manifest, or set `MAGE_MODEL_ROOT` so relative manifest paths resolve against it. Example reference manifest: `configs/mage-flow-turbo-q8-reference.json`.

```bash
mageflow-native verify --manifest configs/mage-flow-turbo-q8-reference.json
```

## Generate

```bash
mageflow-native generate \
    --manifest configs/mage-flow-turbo-q8-reference.json \
    --backend cpu --prompt "A small red fox in a quiet green forest" --output output
```

The canonical CPU request is 512×512, seed 42, 4 steps, CFG 1.0, 4 threads.

## Serve the REST API

```bash
mageflow-native serve --manifest configs/mage-flow-turbo-q8-reference.json \
    --host 127.0.0.1 --port 8090
```

See [docs/REST-API.md](docs/REST-API.md).
