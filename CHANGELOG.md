# Changelog
[![CI](https://github.com/dangkhoa2016/Mage-Flow-Turbo-CPU/actions/workflows/ci.yml/badge.svg)](https://github.com/dangkhoa2016/Mage-Flow-Turbo-CPU/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/dangkhoa2016/Mage-Flow-Turbo-CPU?display_name=tag)](https://github.com/dangkhoa2016/Mage-Flow-Turbo-CPU/releases/tag/v1.0.0)
[![License](https://img.shields.io/github/license/dangkhoa2016/Mage-Flow-Turbo-CPU)](LICENSE)
![Kaggle](https://img.shields.io/badge/Kaggle-CPU%2FRAM--only-20BEFF?logo=kaggle&logoColor=white)

> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](CHANGELOG.vi.md)

## v1.0.0 — 2026-09-02
- Published release. Fresh Kaggle Restart Session → Run All qualification is PASS; the full static contract suite is PASS.
- Git history is `main` with canonical author/committer identity; stale `master` is explicitly removed after the protected backup bundle is created.
- Replaces the heavyweight VAE attachment boundary with the independently verified dedicated VAE-only input.
- Adds dynamic SHA-based input resolution with no legacy full-variation fallback.
- Adds profile-driven local REST, bilingual repository-first notebook, optional authenticated gateway, evidence/CI contracts, and one-real-acceptance policy.
- Adds evidence semantics that derive/cross-check actual evidence files, persists seed/exit code/elapsed time, and keeps raw `argv.json` excluded from publication evidence.
- Adds a 16-case actual-evidence mutation matrix in addition to the frozen 30-case contract negative matrix.
- Phase E/E.1 remain frozen historical evidence; PyTorch v0.1.2 remains reference-only.
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
