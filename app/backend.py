from __future__ import annotations
from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import threading
import time
import uuid
from .artifacts import inspect_png, write_fake_rgb_png
from .config import ServiceConfig
from .profiles import Profile
from .telemetry import read_proc_rss_kb, read_mem_available_kb

@dataclass
class GenerationResult:
    request_id: str
    profile: str
    seed: int
    exit_code: int
    elapsed_ms: int
    peak_sd_cli_rss_kb: int | None
    minimum_mem_available_kb: int | None
    artifact: dict
    stdout_path: str
    stderr_path: str


def build_sd_cli_argv(config: ServiceConfig, *, prompt: str, seed: int, profile: Profile, output_path: str) -> list[str]:
    return [
        config.sd_cli, "--backend", "cpu", "--params-backend", "cpu",
        "--diffusion-model", config.dit_q8, "--llm", config.qwen, "--vae", config.vae,
        "-p", prompt, "--cfg-scale", f"{profile.cfg_scale:.1f}", "--steps", str(profile.steps),
        "-W", str(profile.width), "-H", str(profile.height), "-s", str(seed), "-t", str(profile.threads),
        "--diffusion-fa", "--output", output_path,
    ]

def _safe_request_id(client_request_id: str | None) -> str:
    return client_request_id or f"release-{uuid.uuid4().hex[:12]}"

def generate(config: ServiceConfig, *, prompt: str, seed: int, profile: Profile, client_request_id: str | None = None, fake: bool = False) -> GenerationResult:
    request_id = _safe_request_id(client_request_id)
    run_dir = Path(config.runs_dir) / request_id
    run_dir.mkdir(parents=True, exist_ok=False)
    output_path = Path(config.output_dir) / f"{request_id}.png"
    stdout_path = run_dir / "stdout.log"
    stderr_path = run_dir / "stderr.log"
    request_doc = {"prompt": prompt, "seed": seed, "client_request_id": client_request_id, "profile": profile.name}
    (run_dir / "request.json").write_text(json.dumps(request_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    start = time.monotonic()
    peak_rss = None
    min_avail = None
    exit_code = 0
    if fake:
        write_fake_rgb_png(output_path, profile.width, profile.height)
        stdout_path.write_text("FAKE_BACKEND=PASS\n", encoding="utf-8")
        stderr_path.write_text("", encoding="utf-8")
    else:
        argv = build_sd_cli_argv(config, prompt=prompt, seed=seed, profile=profile, output_path=str(output_path))
        # Full argv is raw run evidence only and intentionally excluded from release evidence collectors.
        (run_dir / "argv.json").write_text(json.dumps(argv, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        with stdout_path.open("wb") as out, stderr_path.open("wb") as err:
            proc = subprocess.Popen(argv, stdout=out, stderr=err, shell=False, start_new_session=True)
            timeout_seconds = min(profile.timeout_seconds, config.timeout_seconds)
            deadline = time.monotonic() + timeout_seconds
            while proc.poll() is None:
                rss = read_proc_rss_kb(proc.pid)
                avail = read_mem_available_kb()
                peak_rss = rss if rss is not None and (peak_rss is None or rss > peak_rss) else peak_rss
                min_avail = avail if avail is not None and (min_avail is None or avail < min_avail) else min_avail
                if time.monotonic() > deadline:
                    proc.terminate()
                    try: proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill(); proc.wait(timeout=5)
                    raise TimeoutError(f"sd-cli exceeded profile timeout {timeout_seconds}s")
                time.sleep(0.5)
            exit_code = int(proc.returncode or 0)
        if exit_code != 0:
            raise RuntimeError(f"sd-cli exited with code {exit_code}; see {stderr_path}")
    artifact = inspect_png(output_path, profile.width, profile.height)
    elapsed_ms = int((time.monotonic() - start) * 1000)
    result = GenerationResult(request_id, profile.name, seed, exit_code, elapsed_ms, peak_rss, min_avail, artifact, str(stdout_path), str(stderr_path))
    telemetry={"elapsed_ms": elapsed_ms, "peak_sd_cli_rss_kb": peak_rss, "minimum_mem_available_kb": min_avail}
    (run_dir / "telemetry.json").write_text(json.dumps(telemetry, indent=2) + "\n")
    stored_result={
        "request_id":request_id,"status":"succeeded","profile":profile.name,"seed":seed,
        "exit_code":exit_code,"elapsed_ms":elapsed_ms,"artifact":artifact,
    }
    (run_dir / "result.json").write_text(json.dumps(stored_result, indent=2) + "\n")
    return result
