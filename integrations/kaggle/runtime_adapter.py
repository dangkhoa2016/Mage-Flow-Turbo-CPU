from __future__ import annotations

import os
from pathlib import Path

from mageflow_native.config import default_runtime_root


def kaggle_cache_root() -> Path:
    if os.environ.get("MAGE_RUNTIME_ROOT"):
        return Path(os.environ["MAGE_RUNTIME_ROOT"]).expanduser()
    work = Path("/kaggle/working")
    if work.is_dir():
        return work / ".mageflow-native"
    return default_runtime_root()


def runtime_hint(backend: str) -> str | None:
    hint = os.environ.get("MAGE_SD_CLI")
    if hint:
        return hint
    if backend == "cpu":
        probe = os.environ.get("MAGE_CPU_PREBUILT_SD_CLI")
        if probe and Path(probe).is_file():
            return probe
    return None
