from __future__ import annotations

import json
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from mageflow_native.inference.command import build_sd_cli_argv
from mageflow_native.models.manifest import ModelManifest, sha256_file
from mageflow_native.runtime.spec import BackendSpec
from mageflow_native.telemetry import read_mem_available_kb, read_proc_rss_kb


@dataclass(frozen=True)
class ArtifactInfo:
    filename: str
    bytes: int
    sha256: str
    width: int
    height: int


@dataclass
class GenerationResult:
    request_id: str
    seed: int
    exit_code: int
    elapsed_ms: int
    peak_sd_cli_rss_kb: int | None
    minimum_mem_available_kb: int | None
    gpu_peak_mib: int | None
    artifact: ArtifactInfo
    stdout_path: str
    stderr_path: str


def _inspect_png(path: Path, expected_width: int, expected_height: int) -> ArtifactInfo:
    import struct
    raw = path.read_bytes()
    if len(raw) < 33 or not raw.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("invalid PNG signature")
    width, height, bit_depth, color_type, _, _, _ = struct.unpack(">IIBBBBB", raw[16:29])
    if bit_depth != 8 or color_type not in (2, 6):
        raise ValueError("expected 8-bit RGB/RGBA PNG")
    if width != expected_width or height != expected_height:
        raise ValueError(f"unexpected PNG dimensions {width}x{height}")
    return ArtifactInfo(
        filename=path.name,
        bytes=path.stat().st_size,
        sha256=sha256_file(path),
        width=width,
        height=height,
    )


def _safe_request_id(client_request_id: str | None) -> str:
    return client_request_id or f"release-{uuid.uuid4().hex[:12]}"


def _poll_cuda_used_mib(pid: int) -> int | None:
    try:
        result = subprocess.run(
            [
                "nvidia-smi", "--query-compute-apps=pid,used_memory",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    used = None
    for line in result.stdout.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) == 2:
            try:
                if int(parts[0]) == pid:
                    mib = int(parts[1])
                    used = mib if used is None or mib > used else used
            except ValueError:
                continue
    return used


def run_generation(
    sd_cli: str | Path,
    manifest: ModelManifest,
    backend_spec: BackendSpec,
    *,
    prompt: str,
    seed: int,
    width: int = 512,
    height: int = 512,
    steps: int = 4,
    cfg_scale: float = 1.0,
    threads: int = 4,
    output_dir: str | Path,
    runs_dir: str | Path,
    client_request_id: str | None = None,
    timeout_seconds: int = 2700,
    collect_cuda: bool = False,
    fake: bool = False,
) -> GenerationResult:
    request_id = _safe_request_id(client_request_id)
    run_dir = Path(runs_dir) / request_id
    run_dir.mkdir(parents=True, exist_ok=False)
    output_path = Path(output_dir) / f"{request_id}.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_path = run_dir / "stdout.log"
    stderr_path = run_dir / "stderr.log"

    model_paths = {
        "diffusion": manifest.diffusion.path,
        "text_encoder": manifest.text_encoder.path,
        "vae": manifest.vae.path,
    }
    (run_dir / "request.json").write_text(
        json.dumps(
            {
                "prompt": prompt,
                "seed": seed,
                "client_request_id": client_request_id,
                "backend": backend_spec.backend,
                "params_backend": backend_spec.params_backend,
                "profile": "demo",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    start = time.monotonic()
    peak_rss: int | None = None
    min_avail: int | None = None
    gpu_peak_mib: int | None = None
    exit_code = 0

    if fake:
        from mageflow_native.inference._fake import write_fake_rgb_png
        write_fake_rgb_png(output_path, width, height)
        stdout_path.write_text("FAKE_BACKEND=PASS\n", encoding="utf-8")
        stderr_path.write_text("", encoding="utf-8")
    else:
        argv = build_sd_cli_argv(
            sd_cli,
            model_paths=model_paths,
            backend_spec=backend_spec,
            prompt=prompt,
            seed=seed,
            steps=steps,
            cfg_scale=cfg_scale,
            width=width,
            height=height,
            threads=threads,
            output_path=output_path,
        )
        (run_dir / "argv.json").write_text(
            json.dumps(argv, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        with stdout_path.open("wb") as out, stderr_path.open("wb") as err:
            proc = subprocess.Popen(
                argv,
                stdout=out,
                stderr=err,
                shell=False,
                start_new_session=True,
            )
            deadline = time.monotonic() + timeout_seconds
            while proc.poll() is None:
                rss = read_proc_rss_kb(proc.pid)
                avail = read_mem_available_kb()
                peak_rss = rss if rss is not None and (peak_rss is None or rss > peak_rss) else peak_rss
                min_avail = avail if avail is not None and (min_avail is None or avail < min_avail) else min_avail
                if collect_cuda:
                    gpu = _poll_cuda_used_mib(proc.pid)
                    gpu_peak_mib = gpu if gpu is not None and (gpu_peak_mib is None or gpu > gpu_peak_mib) else gpu_peak_mib
                if time.monotonic() > deadline:
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait(timeout=5)
                    raise TimeoutError(f"sd-cli exceeded timeout {timeout_seconds}s")
                time.sleep(0.5)
            exit_code = int(proc.returncode or 0)
        if exit_code != 0:
            raise RuntimeError(f"sd-cli exited with code {exit_code}; see {stderr_path}")

    artifact = _inspect_png(output_path, width, height)
    elapsed_ms = int((time.monotonic() - start) * 1000)
    (run_dir / "telemetry.json").write_text(
        json.dumps(
            {
                "elapsed_ms": elapsed_ms,
                "peak_sd_cli_rss_kb": peak_rss,
                "minimum_mem_available_kb": min_avail,
                "gpu_peak_mib": gpu_peak_mib,
            },
            indent=2,
        )
        + "\n"
    )
    result = GenerationResult(
        request_id=request_id,
        seed=seed,
        exit_code=exit_code,
        elapsed_ms=elapsed_ms,
        peak_sd_cli_rss_kb=peak_rss,
        minimum_mem_available_kb=min_avail,
        gpu_peak_mib=gpu_peak_mib,
        artifact=artifact,
        stdout_path=str(stdout_path),
        stderr_path=str(stderr_path),
    )
    (run_dir / "result.json").write_text(
        json.dumps(
            {
                "request_id": request_id,
                "status": "succeeded",
                "seed": seed,
                "exit_code": exit_code,
                "elapsed_ms": elapsed_ms,
                "artifact": {
                    "filename": artifact.filename,
                    "bytes": artifact.bytes,
                    "sha256": artifact.sha256,
                    "width": artifact.width,
                    "height": artifact.height,
                },
            },
            indent=2,
        )
        + "\n"
    )
    return result
