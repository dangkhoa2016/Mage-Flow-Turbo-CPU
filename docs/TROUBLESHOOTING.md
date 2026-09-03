# Troubleshooting
[![CI](https://github.com/dangkhoa2016/Mage-Flow-Turbo-CPU/actions/workflows/ci.yml/badge.svg)](https://github.com/dangkhoa2016/Mage-Flow-Turbo-CPU/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/dangkhoa2016/Mage-Flow-Turbo-CPU?display_name=tag)](https://github.com/dangkhoa2016/Mage-Flow-Turbo-CPU/releases/tag/v1.0.0)
[![License](https://img.shields.io/github/license/dangkhoa2016/Mage-Flow-Turbo-CPU)](LICENSE)
![Kaggle](https://img.shields.io/badge/Kaggle-CPU%2FRAM--only-20BEFF?logo=kaggle&logoColor=white)

> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](TROUBLESHOOTING.vi.md)

## Retry rule
Before `sd-cli` starts, recoverable bootstrap/path/port problems may be corrected and the gate rerun. After the canonical real `sd-cli` has started, **do not automatically run another real image**; preserve evidence and stop for review unless the user explicitly starts a new acceptance later.

| Code | Recovery | Real retry? |
|---|---|---|
| MODEL_MOUNT_MISSING | Correct attached Kaggle variations; rerun discovery/preflight. | Yes, only if real inference never started |
| MODEL_HASH_MISMATCH | Stop; verify model/version identity. Never substitute another quantization. | No automatic retry |
| VAE_ONLY_AMBIGUOUS | Detach duplicate VAE-only versions until exactly one candidate remains. | Yes before inference |
| SD_CLI_MISSING | Rerun pinned CPU bootstrap. | Yes before inference |
| RUNTIME_COMMIT_MISMATCH | Delete only runtime build and rebuild exact pinned commit. | Yes before inference |
| BUILD_FAILED | Inspect CMake/compiler/disk logs; do not change upstream commit. | Yes before inference |
| INSUFFICIENT_MEM_AVAILABLE | Stop unnecessary processes or start a fresh CPU session. | Yes before inference |
| INSUFFICIENT_DISK | Remove disposable runtime/cache, never Kaggle inputs. | Yes before inference |
| PORT_ALREADY_IN_USE | Identify owner; never kill an unowned service automatically. | Yes before inference |
| SERVER_NOT_READY | Inspect server stderr/preflight; do not issue generation. | Yes before inference |
| BUSY_SINGLE_FLIGHT | Wait for the active request; do not start a parallel backend. | Not a retry of active request |
| REQUEST_TIMEOUT | Preserve run logs/output; stop for review. | No automatic retry |
| SD_CLI_EXIT_NONZERO | Preserve stdout/stderr/result and classify failure. | No automatic retry |
| INVALID_PNG | Preserve bytes and backend logs; never re-encode as a “repair”. | No automatic retry |
| ARTIFACT_HASH_MISMATCH | Preserve both copies and metadata. | No automatic retry |
| ORPHAN_SD_CLI | Stop owned child only after PID/cmdline verification. | No automatic retry |
| CLOUDFLARED_MISSING | Optional only: install/provide `CLOUDFLARED_BIN`, or leave public mode NOT_RUN. | No inference needed |
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


## Evidence / Git provenance failures
| Code | Recovery | Real retry? |
|---|---|---|
| ACTUAL_EVIDENCE_SEMANTIC_MISMATCH | Preserve the evidence tree; compare preflight/local/request/result/telemetry. Never edit evidence to manufacture PASS. | No inference needed |
| CANONICAL_RUN_EVIDENCE_MISSING | Correct collector/source. Required: request/stdout/stderr/telemetry/result. `argv.json` remains excluded. | No inference needed |
| REPO_ORIGIN_DISALLOWED_MARKER | Finalize the origin only from the real official GitHub URL; never ship a placeholder origin. | No inference needed |
| REPO_ORIGIN_PENDING | Do not invent an origin; finalize only from the real official GitHub URL. | No inference needed |
