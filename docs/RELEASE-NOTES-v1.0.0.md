# Mage-Flow-Turbo-CPU v1.0.0 Release Notes
[![CI](https://github.com/dangkhoa2016/Mage-Flow-Turbo-CPU/actions/workflows/ci.yml/badge.svg)](https://github.com/dangkhoa2016/Mage-Flow-Turbo-CPU/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/dangkhoa2016/Mage-Flow-Turbo-CPU?display_name=tag)](https://github.com/dangkhoa2016/Mage-Flow-Turbo-CPU/releases/tag/v1.0.0)
[![License](https://img.shields.io/github/license/dangkhoa2016/Mage-Flow-Turbo-CPU)](LICENSE)
![Kaggle](https://img.shields.io/badge/Kaggle-CPU%2FRAM--only-20BEFF?logo=kaggle&logoColor=white)

> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](RELEASE-NOTES-v1.0.0.vi.md)

## What this is

Mage-Flow-Turbo-CPU is a repository-first Kaggle CPU/RAM-only production-oriented demo built on a frozen stable-diffusion.cpp + GGUF technical stack. v1.0.0, released on 2026-09-04, is the first public release of this lineage.

## Highlights

- Portable CPU-only local REST lifecycle with fail-closed packaging.
- Exact input identity verification against the frozen technical contract.
- One canonical 512 real acceptance from a fresh Kaggle notebook (no auto-retry after `sd-cli` begins).
- Verified prebuilt CPU runtime delivery from a public Kaggle dataset, with source-build fallback for public `auto` mode and fail-closed `prebuilt` acceptance mode.
- Optional authenticated Quick Tunnel without direct backend exposure.
- Bilingual English/Vietnamese UX and UTF-8 transport.
- Sanitized evidence and a full static contract suite with contract and actual-evidence negative matrices.

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

## Public runtime dataset

`dangkhoa2016/stable-diffusion-cpp-6b3edaa-portable-cpu-runtime`

Verified `sd-cli` SHA-256:

`7539d90b99eaf2b6279eec4f9006a68ae53e87bfe0c9c325ff3f329220468a5c`

## Quick start

Attach the four required Kaggle inputs (public prebuilt CPU runtime dataset + DiT q8-0 + VAE-only + Qwen q4-k-m), finalize the GitHub origin, import `notebooks/kaggle-cpu-production-demo.ipynb`, choose **Restart Session -> Run All**, and keep defaults.

`RUN_LIVE_DEMO=True`, `ENABLE_PUBLIC_TUNNEL=False`, `RUN_OPTIONAL_USER_GENERATION=False`, `MAGE_PROFILE="demo"`.

## Baseline

v1.0.0 is published from the final qualified source tree on `main`, tagged as the annotated `v1.0.0` release. It includes the publication-facing documentation, the release publication contract tests, the annotated tag, and the GitHub Release. The canonical 512 PNG and the sanitized production evidence archive are produced by one fresh Kaggle `Restart Session -> Run All` qualification on that exact source tree; their SHA-256 digests are recorded in the generated evidence archive for independent verification.

## License

This release is licensed under the **MIT License**. Copyright (c) 2026 `Đăng Khoa <i.am@dangkhoa.dev>`. See the `LICENSE` file for the full text. The owner explicitly selected MIT; the license is not inferred from upstream components.
