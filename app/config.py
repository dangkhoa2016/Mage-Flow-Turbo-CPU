from __future__ import annotations
from dataclasses import dataclass
import os
from pathlib import Path
from .profiles import load_profile

@dataclass(frozen=True)
class ServiceConfig:
    sd_cli: str
    dit_q8: str
    qwen: str
    vae: str
    output_dir: str
    runs_dir: str
    host: str = "127.0.0.1"
    port: int = 8090
    timeout_seconds: int = 2700

    def ensure_safe(self) -> None:
        if self.host != "127.0.0.1":
            raise ValueError("backend must bind only to 127.0.0.1")
        if self.port != 8090 and os.environ.get("MAGE_ALLOW_ALT_PORT", "0") != "1":
            raise ValueError("canonical backend port is 8090")
        for d in (self.output_dir, self.runs_dir):
            Path(d).mkdir(parents=True, exist_ok=True)

ALLOWED_FIELDS = {"prompt", "seed", "client_request_id", "profile"}

def validate_generation_payload(payload: object) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("JSON body must be an object")
    unknown = set(payload) - ALLOWED_FIELDS
    if unknown:
        raise ValueError(f"unknown fields: {sorted(unknown)}")
    prompt = payload.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt must be a non-empty UTF-8 string")
    if len(prompt) > 2000:
        raise ValueError("prompt exceeds 2000 characters")
    seed = payload.get("seed", 42)
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0 or seed > 2**32 - 1:
        raise ValueError("seed must be an integer in [0, 2^32-1]")
    client_request_id = payload.get("client_request_id")
    if client_request_id is not None:
        if not isinstance(client_request_id, str) or not client_request_id or len(client_request_id) > 128:
            raise ValueError("client_request_id must be 1..128 characters")
        if any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for c in client_request_id):
            raise ValueError("client_request_id contains unsafe characters")
    profile = payload.get("profile", "demo")
    load_profile(profile)
    return {"prompt": prompt, "seed": seed, "client_request_id": client_request_id, "profile": profile}
