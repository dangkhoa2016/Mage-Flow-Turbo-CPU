from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .artifacts import sha256_file
from .constants import *

class InputResolutionError(RuntimeError): pass

@dataclass(frozen=True)
class ResolvedInput:
    path: Path
    bytes: int
    sha256: str


def _norm(p: Path) -> str:
    return p.as_posix().lower()

def resolve_exact_input(root: Path, *, filename: str, required_fragment: str, forbidden_fragment: str | None, expected_size: int | None, expected_sha256: str) -> ResolvedInput:
    root = Path(root)
    required = required_fragment.lower().strip('/')
    forbidden = forbidden_fragment.lower() if forbidden_fragment else None
    candidates=[]
    for p in root.rglob(filename):
        n=_norm(p)
        if required not in n: continue
        if forbidden and forbidden in n: continue
        candidates.append(p)
    if len(candidates) != 1:
        raise InputResolutionError(f"expected exactly one {filename} under *{required_fragment}*, found {len(candidates)}")
    p=candidates[0].resolve()
    n=_norm(p)
    if forbidden and forbidden in n:
        raise InputResolutionError(f"forbidden input path: {p}")
    size=p.stat().st_size
    if expected_size is not None and size != expected_size:
        raise InputResolutionError(f"size mismatch for {p.name}: {size} != {expected_size}")
    digest=sha256_file(p)
    if digest != expected_sha256:
        raise InputResolutionError(f"SHA256 mismatch for {p.name}: {digest}")
    return ResolvedInput(p,size,digest)

def resolve_canonical_inputs(root: Path = Path('/kaggle/input')) -> dict[str, ResolvedInput]:
    dit=resolve_exact_input(root, filename=DIT_FILENAME, required_fragment=DIT_VARIATION_HINT, forbidden_fragment=None, expected_size=DIT_BYTES, expected_sha256=DIT_SHA256)
    qwen=resolve_exact_input(root, filename=QWEN_FILENAME, required_fragment=QWEN_VARIATION_HINT, forbidden_fragment=None, expected_size=None, expected_sha256=QWEN_SHA256)
    vae=resolve_exact_input(root, filename=VAE_FILENAME, required_fragment=VAE_VARIATION_HINT, forbidden_fragment='/pytorch/default/', expected_size=VAE_BYTES, expected_sha256=VAE_SHA256)
    # Belt-and-suspenders: the canonical VAE may never come from pytorch/default.
    if '/pytorch/default/' in _norm(vae.path):
        raise InputResolutionError('pytorch/default is forbidden for release evidence')
    return {'dit':dit,'qwen':qwen,'vae':vae}
