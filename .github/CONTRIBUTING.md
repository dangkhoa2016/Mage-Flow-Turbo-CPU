# Contributing

Thank you for your interest in Mage-Flow-Turbo-CPU.

## Before opening a change

- Keep the project CPU/RAM-only on the default Kaggle path.
- Do not add model weights or generated runtime archives to Git.
- Do not change the pinned model/runtime hashes without a separately reviewed qualification.
- Preserve loopback-only inference backend binding.
- Add or update tests for contract changes.

## Local checks

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile app/*.py scripts/*.py scripts/kaggle/*.py
for f in scripts/*.sh scripts/kaggle/*.sh; do [ -f "$f" ] && bash -n "$f"; done
python3 -m json.tool notebooks/kaggle-cpu-production-demo.ipynb >/dev/null
python3 scripts/publication_surface_audit.py --root .
```

Use focused, descriptive commit subjects. Do not include credentials, private URLs, or generated evidence containing secrets.
