from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

from mageflow_native import PRODUCT_NAME, __version__
from mageflow_native.config import default_model_root, default_runtime_root
from mageflow_native.constants import (
    CANONICAL_CFG,
    CANONICAL_HEIGHT,
    CANONICAL_PROMPT,
    CANONICAL_SEED,
    CANONICAL_STEPS,
    CANONICAL_THREADS,
    CANONICAL_WIDTH,
    SDCPP_COMMIT,
)
from mageflow_native.models.manifest import load_manifest, verify_manifest
from mageflow_native.runtime.manager import RuntimeManager
from mageflow_native.runtime.spec import BackendSpec, RuntimeBuildBackend


def _resolve_runtime(args) -> RuntimeManager:
    runtime_root = Path(args.runtime_root)
    explicit = args.sd_cli or os.environ.get("MAGE_SD_CLI")
    return RuntimeManager(runtime_root, explicit_sd_cli=explicit)


def _load_manifest(args):
    model_root = args.model_root or default_model_root()
    return load_manifest(args.manifest, model_root=model_root)


def cmd_doctor(args) -> int:
    runtime_root = Path(args.runtime_root)
    manager = _resolve_runtime(args)
    manifest_path = Path(args.manifest)
    data = {
        "product": PRODUCT_NAME,
        "version": __version__,
        "os": platform.system(),
        "platform": platform.platform(),
        "arch": platform.machine(),
        "python": platform.python_version(),
        "runtime_root": str(runtime_root),
        "manifest": str(manifest_path),
        "runtime_commit": SDCPP_COMMIT,
        "chosen_backend": args.backend,
    }
    try:
        sd_cli = manager.resolve()
        data["runtime_path"] = str(sd_cli)
        identity = manager.verify(sd_cli, requested_backend=args.backend)
        data["runtime_version"] = identity.version_output
        data["devices"] = identity.devices_output
        data["runtime_verified"] = True
    except Exception as exc:
        data["runtime_path"] = None
        data["runtime_verified"] = False
        data["runtime_error"] = str(exc)
        data["devices"] = None
    try:
        manifest = _load_manifest(args)
        comps = {
            "diffusion": manifest.diffusion.path.name,
            "text_encoder": manifest.text_encoder.path.name,
            "vae": manifest.vae.path.name,
        }
        verified = verify_manifest(manifest)
        data["manifest_loaded"] = True
        data["components"] = comps
        data["verified"] = {k: str(v) for k, v in verified.items()}
    except Exception as exc:
        data["manifest_loaded"] = False
        data["manifest_error"] = str(exc)
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        for key, value in data.items():
            if key == "devices" and value:
                print(f"{key}:")
                for line in value.splitlines():
                    print(f"  {line}")
            else:
                print(f"{key}: {value}")
    return 0


def cmd_verify(args) -> int:
    manifest = _load_manifest(args)
    verified = verify_manifest(manifest)
    manager = _resolve_runtime(args)
    sd_cli = manager.resolve()
    identity = manager.verify(sd_cli, requested_backend=args.backend)
    result = {
        "verified_models": {k: str(v) for k, v in verified.items()},
        "runtime": identity.path,
        "runtime_commit": identity.pinned_commit,
        "backend": args.backend,
        "ok": True,
    }
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"models_verified: {list(verified.keys())}")
        print(f"runtime: {identity.path}")
        print(f"backend: {args.backend}")
        print("verify: PASS")
    return 0


def cmd_generate(args) -> int:
    from mageflow_native.constants import DIT_SHA256
    manifest = _load_manifest(args)
    verify_manifest(manifest)
    manager = _resolve_runtime(args)
    sd_cli = manager.resolve()
    backend_spec = BackendSpec(
        backend=args.backend,
        params_backend=args.params_backend,
        max_vram=args.max_vram,
        split_mode=args.split_mode,
        auto_fit=args.auto_fit,
    )
    from mageflow_native.inference.runner import run_generation
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    result = run_generation(
        sd_cli,
        manifest,
        backend_spec,
        prompt=args.prompt,
        seed=args.seed,
        width=args.width,
        height=args.height,
        steps=args.steps,
        cfg_scale=args.cfg_scale,
        threads=args.threads,
        output_dir=output_dir,
        runs_dir=output_dir / ".runs",
        client_request_id=args.request_id,
        timeout_seconds=args.timeout,
        collect_cuda=(args.backend == "cuda0"),
    )
    summary = {
        "status": "succeeded",
        "request_id": result.request_id,
        "seed": result.seed,
        "elapsed_ms": result.elapsed_ms,
        "backend": args.backend,
        "artifact": {
            "filename": result.artifact.filename,
            "bytes": result.artifact.bytes,
            "sha256": result.artifact.sha256,
            "width": result.artifact.width,
            "height": result.artifact.height,
        },
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


def cmd_serve(args) -> int:
    manifest = _load_manifest(args)
    verify_manifest(manifest)
    manager = _resolve_runtime(args)
    sd_cli = manager.resolve()
    backend_spec = BackendSpec(backend=args.backend, params_backend=args.params_backend)
    from mageflow_native.inference.runner import run_generation
    from mageflow_native.service.http import build_server

    output_dir = Path(args.output)
    runs_dir = output_dir / ".runs"
    config = {
        "host": args.host,
        "port": args.port,
        "sd_cli": str(sd_cli),
        "manifest": manifest,
        "output_dir": str(output_dir),
        "runs_dir": str(runs_dir),
        "timeout_seconds": args.timeout,
        "backend": args.backend,
    }
    if args.host != "127.0.0.1" and os.environ.get("MAGE_ALLOW_PUBLIC_BIND", "0") != "1":
        print("serve: backend must bind only to 127.0.0.1 unless MAGE_ALLOW_PUBLIC_BIND=1", file=sys.stderr)
        return 2
    server = build_server(config, fake=args.fake)
    print(f"serving on http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def cmd_runtime(args) -> int:
    build_backend = RuntimeBuildBackend(args.backend)
    manager = _resolve_runtime(args)
    sd_cli = manager.build(build_backend)
    identity = manager.verify(sd_cli, requested_backend=args.backend)
    result = {
        "runtime_path": identity.path,
        "runtime_commit": identity.pinned_commit,
        "version": identity.version_output,
        "backend": args.backend,
        "ok": True,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mageflow-native",
        description=f"{PRODUCT_NAME} native inference CLI",
    )
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command")

    def add_common(p):
        p.add_argument("--manifest", default=os.environ.get("MAGE_MODEL_MANIFEST", "configs/mage-flow-turbo-q8-reference.json"))
        p.add_argument("--model-root", default=None)
        p.add_argument("--sd-cli", default=None)
        p.add_argument("--runtime-root", default=str(default_runtime_root()))
        p.add_argument("--json", action="store_true")

    doctor = sub.add_parser("doctor", help="show system and configuration status")
    add_common(doctor)
    doctor.add_argument("--backend", default="auto")

    verify = sub.add_parser("verify", help="verify runtime and model identities")
    add_common(verify)
    verify.add_argument("--backend", default="auto")

    generate = sub.add_parser("generate", help="generate one image")
    add_common(generate)
    generate.add_argument("--backend", default="cpu")
    generate.add_argument("--params-backend", default=None)
    generate.add_argument("--max-vram", default=None)
    generate.add_argument("--split-mode", default=None)
    generate.add_argument("--auto-fit", action="store_true")
    generate.add_argument("--prompt", default=CANONICAL_PROMPT)
    generate.add_argument("--seed", type=int, default=CANONICAL_SEED)
    generate.add_argument("--width", type=int, default=CANONICAL_WIDTH)
    generate.add_argument("--height", type=int, default=CANONICAL_HEIGHT)
    generate.add_argument("--steps", type=int, default=CANONICAL_STEPS)
    generate.add_argument("--cfg-scale", type=float, default=CANONICAL_CFG)
    generate.add_argument("--threads", type=int, default=CANONICAL_THREADS)
    generate.add_argument("--output", default="output")
    generate.add_argument("--request-id", default=None)
    generate.add_argument("--timeout", type=int, default=2700)

    serve = sub.add_parser("serve", help="start loopback REST service")
    add_common(serve)
    serve.add_argument("--backend", default="auto")
    serve.add_argument("--params-backend", default=None)
    serve.add_argument("--output", default="output")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8090)
    serve.add_argument("--timeout", type=int, default=2700)
    serve.add_argument("--fake", action="store_true")

    runtime = sub.add_parser("runtime", help="build/verify the native runtime")
    runtime.add_argument("--runtime-root", default=str(default_runtime_root()))
    runtime.add_argument("--json", action="store_true")
    rsub = runtime.add_subparsers(dest="runtime_command")
    buildp = rsub.add_parser("build", help="build the pinned native runtime")
    buildp.add_argument("--backend", choices=["cpu", "cuda"], required=True)
    buildp.add_argument("--json", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.command:
        build_parser().print_help()
        return 2
    if args.command == "doctor":
        return cmd_doctor(args)
    if args.command == "verify":
        return cmd_verify(args)
    if args.command == "generate":
        return cmd_generate(args)
    if args.command == "serve":
        return cmd_serve(args)
    if args.command == "runtime":
        if hasattr(args, "runtime_command") and args.runtime_command == "build":
            return cmd_runtime(args)
        build_parser().print_help()
        return 2
    build_parser().print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
