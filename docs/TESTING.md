# Testing

Mage-Flow-Turbo-Native-Inference is tested through unit/contract tests (no real model weights), static publication audits, and real qualification gates.

## Static suite (no model weights)

```bash
python -m pip install -e .
python -m pytest tests/ -q
```

Covered contracts:

- model manifest validation and SHA verification (`tests/unit/test_manifest.py`)
- backend/placement validation (`tests/unit/test_runtime_spec.py`)
- runtime manager resolution and identity (`tests/unit/test_runtime_manager.py`)
- inference argv construction and runner (`tests/unit/test_inference_*.py`)
- REST API contracts (`tests/contracts/test_rest_api.py`)
- CLI contracts and secret-safe doctor output (`tests/contracts/test_cli_contract.py`, `tests/unit/test_cli_doctor.py`)
- no-Kaggle-core dependency (`tests/contracts/test_no_kaggle_core_dependency.py`)
- notebook contract (`tests/contracts/test_notebook_contract.py`)
- qualification harnesses (`tests/contracts/test_qualification_contract.py`)
- publication surface (`tests/contracts/test_publication_surface.py`)
- Kaggle adapter (`tests/integration/test_kaggle_adapter.py`)

## Static gates

```bash
python -m compileall -q mageflow_native integrations scripts
python scripts/publication/audit_public_surface.py --root .
for f in $(find scripts -type f -name '*.sh'); do bash -n "$f"; done
python -m json.tool notebooks/kaggle-production-demo.ipynb >/dev/null
```

Expected output includes `PUBLICATION_SURFACE_AUDIT=PASS` and a fully green test suite.

## Canonical CPU acceptance

Requires the three model files, a built/verified CPU `sd-cli`, and a Linux CPU host. Exactly one canonical generation: 512×512, seed 42, 4 steps, CFG 1.0, 4 threads, canonical fox prompt.

```bash
python scripts/qualification/run-canonical.py \
    --backend cpu --manifest MODEL.json --evidence-root evidence-qual \
    --source-head-expected <exact public main sha>
```

The canonical CPU PNG SHA should match the historical reference `c67f3aa4c475f33f5fcecb58392b0a21d1cd82d4d545d5f6e48f59e6a585d819`. If it differs, investigate before accepting.

## NVIDIA CUDA acceptance

Same request, explicit `cuda0`, no silent CPU fallback, valid 512×512 RGB PNG, model hashes, CUDA device proof, RAM/VRAM telemetry, and a recorded CUDA reference PNG SHA (may differ from the CPU bytes).

## Generic local-layout proof

```bash
bash scripts/qualification/run-local-layout-proof.sh \
    --dit <dit-path> --qwen <qwen-path> --vae <vae-path>
```

Runs generic `doctor` + `verify` under `/tmp/mageflow-native-portability-proof` with a non-Kaggle runtime root, proving no Kaggle filesystem dependency.

## Evidence packaging

```bash
python scripts/qualification/package-evidence.py \
    --evidence-root <dir> --output <dir> --label linux-cpu
```

Produces a sanitized `tar.gz` plus sidecar and `MANIFEST.sha256`, failing on secret patterns.
