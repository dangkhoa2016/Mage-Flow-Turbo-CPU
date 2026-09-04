## Summary

Describe the change and why it is needed.

## Validation

- [ ] `python3 -m unittest discover -s tests -v`
- [ ] Python and shell syntax checks pass
- [ ] Notebook JSON validates
- [ ] `python3 scripts/publication_surface_audit.py --root .` passes
- [ ] No model weights or secrets are included
- [ ] Frozen inference/runtime hashes are unchanged, or a separate requalification is attached

## Kaggle impact

State whether this changes the default fresh-session Kaggle path, resource requirements, or real inference behavior.
