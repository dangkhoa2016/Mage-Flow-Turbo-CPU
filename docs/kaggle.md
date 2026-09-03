# Kaggle integration

Kaggle is a **tested adapter/reference environment**, not a required runtime platform. The generic core (`mageflow_native/`) contains no `/kaggle/input` or `/kaggle/working` hard dependencies. Kaggle-specific behavior lives under `integrations/kaggle/` and is a thin adapter over the same generic core.

## What the adapter does

- discovers the mounted canonical model inputs (DiT Q8_0, Qwen Q4_K_M, VAE);
- generates a generic schema-v1 JSON manifest consumed by `mageflow_native/models/manifest.py`;
- selects a Kaggle cache/work directory for the runtime;
- for CPU, may point the generic runtime manager at a verified prebuilt runtime dataset when attached;
- for CUDA, requests the pinned CUDA source-build profile (never the CPU-only binary);
- runs exactly one canonical generation through the generic inference runner;
- collects sanitized evidence.

## Running a fresh CPU session

1. Create a Kaggle Notebook: Internet ON, `Accelerator=None`.
2. Attach the three canonical model inputs plus the verified CPU runtime dataset (recommended).
3. Import `notebooks/kaggle-production-demo.ipynb` from public `main`.
4. Set `QUALIFICATION_BACKEND=cpu`.
5. Choose **Restart Session → Run All**.

The notebook clones the repository, prints `SOURCE_HEAD`, and invokes `integrations/kaggle/qualification.py` which uses the generic manifest/core interfaces.

## Running a fresh CUDA session

1. Create a Kaggle Notebook: Internet ON, T4/T4x2 accelerator.
2. Attach the three canonical model inputs. Do **not** use the CPU-only prebuilt runtime as the CUDA runtime.
3. Import `notebooks/kaggle-production-demo.ipynb` from public `main`.
4. Set `QUALIFICATION_BACKEND=cuda0`.
5. **Restart Session → Run All**.

The generic runtime manager builds/verifies the pinned CUDA `sd-cli` from source and qualifies on explicit `cuda0` with no silent CPU fallback.

## Generic local-layout proof

Separately from the notebook, `scripts/qualification/run-local-layout-proof.sh` proves the core does not depend on Kaggle filesystem conventions: it builds a `/tmp/mageflow-native-portability-proof` layout with symlinked model files, an explicit manifest, and a non-Kaggle runtime root, then runs generic `doctor` + `verify` without invoking `integrations/kaggle`.

## Evidence

Qualification collects sanitized evidence including source head, runtime identity, model hashes, telemetry, artifact SHA and cleanup markers. See `scripts/qualification/package-evidence.py`.
