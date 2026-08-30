from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Profile:
    name: str
    width: int
    height: int
    timeout_seconds: int
    steps: int = 4
    cfg_scale: float = 1.0
    threads: int = 4
    batch: int = 1
    diffusion_fa: bool = True

_PROFILES = {
    "demo": Profile("demo", 512, 512, 900),
    "balanced": Profile("balanced", 640, 640, 1200),
    "research": Profile("research", 1024, 1024, 2700),
}

def load_profile(name: str) -> Profile:
    try: return _PROFILES[name]
    except KeyError as exc: raise ValueError(f"unsupported profile: {name!r}; choose demo, balanced or research") from exc

def primary_profiles() -> dict[str, Profile]: return dict(_PROFILES)
