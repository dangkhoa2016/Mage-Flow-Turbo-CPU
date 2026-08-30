from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import unquote, urlparse

from mageflow_native.constants import (
    DIT_SHA256,
    QWEN_SHA256,
    SDCPP_COMMIT,
    VAE_SHA256,
)
from mageflow_native.inference.runner import run_generation
from mageflow_native.models.manifest import ModelManifest
from mageflow_native.runtime.manager import RuntimeIdentity
from mageflow_native.runtime.spec import BackendSpec
from mageflow_native.service.singleflight import SingleFlight

ALLOWED_FIELDS = {"prompt", "seed", "client_request_id", "backend", "params_backend"}
MAX_JSON_BYTES = 16 * 1024


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
    if (
        isinstance(seed, bool)
        or not isinstance(seed, int)
        or seed < 0
        or seed > 2**32 - 1
    ):
        raise ValueError("seed must be an integer in [0, 2^32-1]")
    client_request_id = payload.get("client_request_id")
    if client_request_id is not None:
        if (
            not isinstance(client_request_id, str)
            or not client_request_id
            or len(client_request_id) > 128
        ):
            raise ValueError("client_request_id must be 1..128 characters")
        if any(
            c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
            for c in client_request_id
        ):
            raise ValueError("client_request_id contains unsafe characters")
    backend = payload.get("backend", "auto")
    params_backend = payload.get("params_backend")
    BackendSpec(backend=backend, params_backend=params_backend)
    return {
        "prompt": prompt,
        "seed": seed,
        "client_request_id": client_request_id,
        "backend": backend,
        "params_backend": params_backend,
    }


class BusyError(RuntimeError):
    pass


class ServiceState:
    def __init__(
        self,
        config: dict,
        *,
        generator,
        fake: bool = False,
    ) -> None:
        self.config = config
        self.generator = generator
        self.fake = fake
        self.singleflight = SingleFlight()
        self.shutting_down = False
        Path(config["output_dir"]).mkdir(parents=True, exist_ok=True)
        Path(config["runs_dir"]).mkdir(parents=True, exist_ok=True)

    @property
    def busy(self) -> bool:
        return self.singleflight.busy

    def generate(self, payload: object):
        data = validate_generation_payload(payload)
        if not self.singleflight.acquire():
            raise BusyError("BUSY_SINGLE_FLIGHT")
        try:
            return self.generator(
                sd_cli=self.config["sd_cli"],
                manifest=self.config["manifest"],
                backend_spec=BackendSpec(
                    backend=data["backend"],
                    params_backend=data["params_backend"],
                ),
                prompt=data["prompt"],
                seed=data["seed"],
                output_dir=self.config["output_dir"],
                runs_dir=self.config["runs_dir"],
                client_request_id=data["client_request_id"],
                timeout_seconds=self.config["timeout_seconds"],
                fake=self.fake,
            )
        finally:
            self.singleflight.release()


class Handler(BaseHTTPRequestHandler):
    server_version = "MageFlowTurbo/1.0"

    def log_message(self, fmt, *args):
        return

    @property
    def state(self) -> ServiceState:
        return self.server.state

    def _send_json(self, status: int, obj: dict) -> None:
        raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _error(self, status: int, code: str, message: str) -> None:
        self._send_json(status, {"status": "error", "error": code, "message": message})

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/healthz":
            return self._send_json(
                200, {"status": "ok", "service": "mage-flow-turbo-native-inference"}
            )
        if path == "/readyz":
            ready = not self.state.shutting_down
            return self._send_json(
                200 if ready else 503,
                {
                    "ready": ready,
                    "busy": self.state.busy,
                    "generation_concurrency": 1,
                },
            )
        if path == "/v1/info":
            return self._send_json(
                200,
                {
                    "service": "mage-flow-turbo-native-inference",
                    "backend": self.state.config.get("backend", "auto"),
                    "runtime_commit": SDCPP_COMMIT,
                    "inputs": {
                        "dit": {"sha256": DIT_SHA256},
                        "qwen": {"sha256": QWEN_SHA256},
                        "vae": {"sha256": VAE_SHA256},
                    },
                    "single_flight": True,
                },
            )
        prefix = "/v1/artifacts/"
        if path.startswith(prefix):
            name = unquote(path[len(prefix):])
            if not name or Path(name).name != name or not name.endswith(".png"):
                return self._error(
                    400, "INVALID_ARTIFACT_NAME", "safe PNG basename required"
                )
            p = (Path(self.state.config["output_dir"]) / name).resolve()
            root = Path(self.state.config["output_dir"]).resolve()
            if p.parent != root or not p.is_file():
                return self._error(404, "ARTIFACT_NOT_FOUND", "artifact not found")
            raw = p.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        self._error(404, "NOT_FOUND", "unknown endpoint")

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/v1/images/generate":
            return self._error(404, "NOT_FOUND", "unknown endpoint")
        try:
            n = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self._error(400, "BAD_LENGTH", "invalid Content-Length")
        if n <= 0 or n > MAX_JSON_BYTES:
            return self._error(
                413 if n > MAX_JSON_BYTES else 400, "BODY_SIZE", "invalid request body size"
            )
        try:
            payload = json.loads(self.rfile.read(n).decode("utf-8"))
            result = self.state.generate(payload)
        except UnicodeDecodeError:
            return self._error(400, "INVALID_UTF8", "body must be UTF-8")
        except json.JSONDecodeError:
            return self._error(400, "INVALID_JSON", "body must be JSON")
        except ValueError as exc:
            return self._error(400, "INVALID_REQUEST", str(exc))
        except BusyError as exc:
            return self._error(409, "BUSY_SINGLE_FLIGHT", str(exc))
        except TimeoutError as exc:
            return self._error(504, "REQUEST_TIMEOUT", str(exc))
        except Exception as exc:
            return self._error(500, "INFERENCE_FAILED", str(exc))
        self._send_json(
            200,
            {
                "status": "succeeded",
                "request_id": result.request_id,
                "width": result.artifact.width,
                "height": result.artifact.height,
                "seed": result.seed,
                "elapsed_ms": result.elapsed_ms,
                "artifact": {
                    "filename": result.artifact.filename,
                    "bytes": result.artifact.bytes,
                    "sha256": result.artifact.sha256,
                },
                "artifact_url": f"/v1/artifacts/{result.artifact.filename}",
            },
        )


class StatefulHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, handler, state):
        self.state = state
        super().__init__(address, handler)


def build_server(
    config: dict,
    *,
    fake: bool = False,
    listen_port: int | None = None,
    generator=run_generation,
    manifest: ModelManifest | None = None,
    runtime_identity: RuntimeIdentity | None = None,
):
    if listen_port is not None:
        config = {**config, "host": "127.0.0.1", "port": listen_port}
    if "manifest" not in config and manifest is not None:
        config = {**config, "manifest": manifest}
    state = ServiceState(config, generator=generator, fake=fake)
    return StatefulHTTPServer((config["host"], config["port"]), Handler, state)
