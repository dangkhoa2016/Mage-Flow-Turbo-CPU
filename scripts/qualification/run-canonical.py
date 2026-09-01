from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from mageflow_native.constants import (
    CANONICAL_CFG,
    CANONICAL_HEIGHT,
    CANONICAL_PROMPT,
    CANONICAL_SEED,
    CANONICAL_STEPS,
    CANONICAL_THREADS,
    CANONICAL_WIDTH,
)
from mageflow_native.inference.runner import run_generation
from mageflow_native.models.manifest import load_manifest, verify_manifest
from mageflow_native.runtime.manager import RuntimeManager
from mageflow_native.runtime.spec import BackendSpec


def _source_head(repo: str | None) -> str | None:
    if not repo:
        return None
    try:
        return (
            subprocess.run(
                ["git", "-C", repo, "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )
            .stdout.strip()
        )
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(prog="run-canonical")
    parser.add_argument("--backend", choices=["cpu", "cuda0"], required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--sd-cli", default=None)
    parser.add_argument("--evidence-root", default="evidence")
    parser.add_argument("--repo", default=None)
    parser.add_argument("--source-head-expected", default=None)
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    verified = verify_manifest(manifest)
    manager = RuntimeManager(Path("/tmp/mageflow-native-canonical-runtime"), explicit_sd_cli=args.sd_cli)
    sd_cli = manager.resolve()
    identity = manager.verify(sd_cli, requested_backend=args.backend)

    head = _source_head(args.repo)
    if args.source_head_expected and head != args.source_head_expected:
        print(f"SOURCE_HEAD_MISMATCH expected={args.source_head_expected} actual={head}", flush=True)
        return 3

    evidence_root = Path(args.evidence_root)
    output_dir = evidence_root / "output"
    runs_dir = evidence_root / "runs"
    backend_spec = BackendSpec(backend=args.backend)
    result = run_generation(
        sd_cli,
        manifest,
        backend_spec,
        prompt=CANONICAL_PROMPT,
        seed=CANONICAL_SEED,
        width=CANONICAL_WIDTH,
        height=CANONICAL_HEIGHT,
        steps=CANONICAL_STEPS,
        cfg_scale=CANONICAL_CFG,
        threads=CANONICAL_THREADS,
        output_dir=output_dir,
        runs_dir=runs_dir,
        client_request_id=f"canonical-{args.backend}",
        timeout_seconds=2700,
        collect_cuda=(args.backend == "cuda0"),
    )

    telemetry = json.loads((runs_dir / f"canonical-{args.backend}" / "telemetry.json").read_text())
    record = {
        "backend": args.backend,
        "backend_spec": {"backend": args.backend, "params_backend": None},
        "runtime": {
            "path": identity.path,
            "commit": identity.pinned_commit,
            "version": identity.version_output,
            "devices": identity.devices_output,
        },
        "models": {
            "diffusion": {
                "filename": verified["diffusion"].name,
                "sha256": manifest.diffusion.sha256,
            },
            "text_encoder": {
                "filename": verified["text_encoder"].name,
                "sha256": manifest.text_encoder.sha256,
            },
            "vae": {
                "filename": verified["vae"].name,
                "sha256": manifest.vae.sha256,
            },
        },
        "request": {
            "prompt": CANONICAL_PROMPT,
            "seed": CANONICAL_SEED,
            "steps": CANONICAL_STEPS,
            "cfg": CANONICAL_CFG,
            "threads": CANONICAL_THREADS,
            "width": CANONICAL_WIDTH,
            "height": CANONICAL_HEIGHT,
            "generation_count": 1,
        },
        "exit_code": result.exit_code,
        "elapsed_ms": result.elapsed_ms,
        "peak_sd_cli_rss_kb": result.peak_sd_cli_rss_kb,
        "gpu_peak_mib": result.gpu_peak_mib,
        "artifact": {
            "filename": result.artifact.filename,
            "bytes": result.artifact.bytes,
            "sha256": result.artifact.sha256,
            "width": result.artifact.width,
            "height": result.artifact.height,
        },
        "source_git_head": head,
    }
    record_path = evidence_root / f"canonical-{args.backend}.json"
    record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
