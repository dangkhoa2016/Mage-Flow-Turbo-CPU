from __future__ import annotations

from pathlib import Path

from mageflow_native.config import default_runtime_root
from mageflow_native.runtime.manager import RuntimeManager
from mageflow_native.runtime.spec import RuntimeBuildBackend


def main() -> int:
    runtime_root = default_runtime_root()
    runtime_root.mkdir(parents=True, exist_ok=True)
    manager = RuntimeManager(runtime_root)
    sd_cli = manager.build(RuntimeBuildBackend("cpu"))
    identity = manager.verify(sd_cli, requested_backend="cpu")
    print(f"BUILD=OK")
    print(f"RUNTIME={identity.path}")
    print(f"VERSION={identity.version_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
