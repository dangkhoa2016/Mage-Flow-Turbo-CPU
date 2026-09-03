# Troubleshooting

## Static/CI failures

- Run `python -m pytest tests/ -q`; fix failing contracts before real qualification if source changed, then rerun CI and keep run IDs.
- `python scripts/publication/audit_public_surface.py --root .` must print `PUBLICATION_SURFACE_AUDIT=PASS`; it fails if the core contains Kaggle paths, model weights are tracked, README lacks required terms, old product identity remains, or workflows are not Actions v7.

## Runtime build

Inspect the exact pinned-source build log and `sd-cli --version` / `--list-devices`. Do not upgrade the runtime pin automatically. A discoverable Mage-Flow-specific defect that requires changing the pin is a new design decision and forces full requalification.

## CUDA

- Verify `nvidia-smi`, CUDA toolkit / `nvcc`, build flags, and `--list-devices`.
- Never fall back silently to CPU when CUDA is requested; fail closed instead.
- OOM on T4: first try explicit mixed placement supported by the pinned runtime (e.g. `diffusion=cuda0,te=cpu,vae=cpu`) while keeping qualification deterministic, and record the topology. If the reference stack cannot qualify on T4 with a defensible topology, stop and report the blocker rather than falsely claiming CUDA support.

## Model resolution

- Print only candidate paths/basenames and expected vs actual SHA; never bypass SHA verification.
- A manifest needs exactly the three components `diffusion`, `text_encoder`, `vae`, each with a valid 64-hex SHA-256 matching the actual file.
- Missing or ambiguous components fail closed.

## History / date mismatch

Do not use the GitHub Contents API for commits (it cannot guarantee requested committer dates). Rebuild the candidate history locally and force-publish the fully verified `main`.

## Evidence / secret finding

Fail closed, regenerate sanitized evidence, and verify clean-room extraction.
