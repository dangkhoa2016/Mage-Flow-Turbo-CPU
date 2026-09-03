# Mage-Flow-Turbo-CPU

[![CI](https://github.com/dangkhoa2016/Mage-Flow-Turbo-CPU/actions/workflows/ci.yml/badge.svg)](https://github.com/dangkhoa2016/Mage-Flow-Turbo-CPU/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/dangkhoa2016/Mage-Flow-Turbo-CPU?display_name=tag)](https://github.com/dangkhoa2016/Mage-Flow-Turbo-CPU/releases/tag/v1.0.0)
[![License](https://img.shields.io/github/license/dangkhoa2016/Mage-Flow-Turbo-CPU)](LICENSE)
![Kaggle](https://img.shields.io/badge/Kaggle-CPU%2FRAM--only-20BEFF?logo=kaggle&logoColor=white)


> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](README.vi.md)

A reproducible **CPU/RAM-only Kaggle demo for Mage-Flow-Turbo**, powered by a pinned `stable-diffusion.cpp` runtime and GGUF model inputs. The project packages a local REST service, a fresh-session Kaggle notebook, resource gates, evidence collection, and an optional authenticated public gateway around one frozen inference contract.

## What this project demonstrates

- CPU-only Mage-Flow-Turbo inference on Kaggle with `Accelerator=None`;
- a portable, verified `sd-cli` runtime with source-build fallback;
- deterministic local REST lifecycle on `127.0.0.1:8090`;
- exactly one canonical real acceptance during the default qualification path;
- bilingual English/Vietnamese notebook UX with UTF-8 transport;
- optional authenticated Quick Tunnel without direct backend exposure;
- fail-closed input verification, evidence packaging, and CI contracts.

This repository is a reproducibility and integration project. It does **not** claim a CPU production latency SLA or benchmark Vietnamese visual quality.

## Quick start on Kaggle

1. Create a fresh Kaggle Notebook with **Internet ON** and **Accelerator=None**.
2. Attach the four required public inputs:
   - portable `stable-diffusion.cpp` CPU runtime dataset;
   - Mage-Flow-Turbo DiT `q8-0`;
   - dedicated VAE-only variation;
   - Qwen `q4-k-m` GGUF input.
3. Import `notebooks/kaggle-cpu-production-demo.ipynb`.
4. Choose **Restart Session → Run All**.
5. Keep the release defaults:

```text
RUN_LIVE_DEMO=True
ENABLE_PUBLIC_TUNNEL=False
RUN_OPTIONAL_USER_GENERATION=False
MAGE_PROFILE="demo"
```

The default qualification profile is 512×512. The 640 profile is optional; 1024 is research/experimental.

## REST surface

```text
GET  /healthz
GET  /readyz
GET  /v1/info
POST /v1/images/generate
GET  /v1/artifacts/<png>
```

The inference backend binds to loopback only. The optional public path uses a separate authenticated gateway.

## Frozen technical contract

```text
stable-diffusion.cpp = 6b3edaaf32cc19e5bb2d819c788bd557eddc8eba
DiT Q8 SHA256         = 4c3dafc143ee64121692b6b63563a4f5288bf6183c4870e1d65f1566519ba7f0
Qwen Q4_K_M SHA256    = 66358cb18bb6b3b1b6675aa412c7a88ef01d228f481184d13668e5201c730a0a
VAE-only SHA256       = 34e076dc1e8a15321e1e07be5111d59cf16dd10b804b7c7e20b4de29013427e0
VAE package            = pytorch/vae-only
profiles               = demo 512 | balanced 640 | research 1024
backend                 = 127.0.0.1:8090 CPU only
auth gateway            = 127.0.0.1:8091 optional
steps / CFG / threads   = 4 / 1.0 / 4
```

Verified public prebuilt runtime dataset:

```text
dangkhoa2016/stable-diffusion-cpp-6b3edaa-portable-cpu-runtime
sd-cli SHA256 = 7539d90b99eaf2b6279eec4f9006a68ae53e87bfe0c9c325ff3f329220468a5c
```

## Release status

`v1.0.0` is the first public release. The current release contract requires the full static suite to pass and one fresh Kaggle **Restart Session → Run All** qualification on the exact published source tree.

## Repository layout

```text
app/                    local REST service and inference orchestration
notebooks/              Kaggle production demo notebook
runtime/                pinned runtime provenance
scripts/                verification and packaging utilities
scripts/kaggle/         Kaggle lifecycle and acceptance utilities
tests/                  static and contract tests
.github/                 CI and community health files
docs/                    user-facing bilingual documentation
```

## Documentation

- [Kaggle production demo](docs/kaggle-production-demo-notebook.md)
- [Testing](docs/TESTING.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Release notes](docs/RELEASE-NOTES-v1.0.0.md)
- [Contributing](.github/CONTRIBUTING.md)
- [Security policy](.github/SECURITY.md)

## License

MIT License. Copyright © 2026 Đăng Khoa <i.am@dangkhoa.dev>.
