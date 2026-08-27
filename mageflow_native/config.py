from __future__ import annotations

import os
from pathlib import Path


def default_runtime_root(env: dict[str, str] | None = None) -> Path:
    e = os.environ if env is None else env
    if e.get("MAGE_RUNTIME_ROOT"):
        return Path(e["MAGE_RUNTIME_ROOT"]).expanduser()
    cache = Path(e.get("XDG_CACHE_HOME", str(Path.home() / ".cache")))
    return cache / "mage-flow-turbo-native"


def default_model_root(env: dict[str, str] | None = None) -> Path | None:
    e = os.environ if env is None else env
    if e.get("MAGE_MODEL_ROOT"):
        return Path(e["MAGE_MODEL_ROOT"]).expanduser()
    return None
