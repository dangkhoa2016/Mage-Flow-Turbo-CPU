import json
import tempfile
import unittest
from pathlib import Path

from app.artifacts import inspect_png, write_fake_rgb_png
from app.constants import (
    CANONICAL_PROMPT,
    CANONICAL_SEED,
    DIT_BYTES,
    DIT_FILENAME,
    DIT_SHA256,
    QWEN_FILENAME,
    QWEN_SHA256,
    SDCPP_COMMIT,
    SDCPP_SHORT,
    VAE_BYTES,
    VAE_FILENAME,
    VAE_SHA256,
)
from app.contracts import baseline_contract_snapshot
from scripts.verify_evidence import EvidenceError, sha, verify


def rebuild_manifests(root: Path) -> None:
    for name in ("MANIFEST.json", "MANIFEST.sha256"):
        try:
            (root / name).unlink()
        except FileNotFoundError:
            pass
    manifest = []
    for p in sorted(root.rglob("*")):
        if p.is_file():
            manifest.append({
                "path": p.relative_to(root).as_posix(),
                "bytes": p.stat().st_size,
                "sha256": sha(p),
            })
    (root / "MANIFEST.json").write_text(json.dumps({"schema_version": 1, "files": manifest}))
    lines = []
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.name != "MANIFEST.sha256":
            lines.append(f"{sha(p)}  {p.relative_to(root).as_posix()}")
    (root / "MANIFEST.sha256").write_text("\n".join(lines) + "\n")


def build_realistic_evidence(root: Path) -> str:
    request_id = "release-acceptance-123"
    (root / "metadata").mkdir(parents=True)
    (root / "artifacts").mkdir()
    run_dir = root / "runs" / request_id
    run_dir.mkdir(parents=True)

    png = root / "artifacts" / "release-acceptance-512.png"
    write_fake_rgb_png(png, 512, 512)
    artifact = inspect_png(png, 512, 512)

    preflight = {
        "status": "PASS",
        "runtime_commit_expected": SDCPP_COMMIT,
        "runtime_version_output": f"stable-diffusion.cpp {SDCPP_SHORT}",
        "runtime_devices_output": "CPU",
        "host": "127.0.0.1",
        "port": 8090,
        "mem_available_kb": 20 * 1024 * 1024,
        "min_mem_available_kb": 16 * 1024 * 1024,
        "disk_free_bytes": 4 * 1024**3,
        "min_disk_free_bytes": 2 * 1024**3,
        "gates": {
            "RELEASE_CPU_ONLY_POLICY": "PASS",
            "RELEASE_MODEL_IDENTITIES": "PASS",
            "RELEASE_SD_CLI_PRESENT": "PASS",
            "RELEASE_RUNTIME_COMMIT": "PASS",
            "RELEASE_RUNTIME_CPU_ONLY": "PASS",
            "RELEASE_MEMORY_GATE": "PASS",
            "RELEASE_DISK_GATE": "PASS",
            "RELEASE_RUNTIME_DIRS_WRITABLE": "PASS",
            "RELEASE_LOCAL_PORT_AVAILABLE": "PASS",
            "RELEASE_SOURCE_NO_MODEL_WEIGHTS": "PASS",
        },
        "inputs": {
            "dit": {"filename": DIT_FILENAME, "bytes": DIT_BYTES, "sha256": DIT_SHA256, "variation": "gguf/q8-0"},
            "qwen": {"filename": QWEN_FILENAME, "bytes": 123, "sha256": QWEN_SHA256, "variation": "gguf/q4-k-m"},
            "vae": {"filename": VAE_FILENAME, "bytes": VAE_BYTES, "sha256": VAE_SHA256, "variation": "pytorch/vae-only"},
        },
    }
    local = {
        "schema_version": 1,
        "mode": "REAL",
        "status": "PASS",
        "profile": "demo",
        "prompt": CANONICAL_PROMPT,
        "seed": CANONICAL_SEED,
        "http_elapsed_ms": 100,
        "request_id": request_id,
        "artifact": artifact,
        "artifact_url_path": f"/v1/artifacts/{request_id}.png",
        "public_tunnel_enabled": False,
    }
    request = {
        "prompt": CANONICAL_PROMPT,
        "seed": CANONICAL_SEED,
        "client_request_id": request_id,
        "profile": "demo",
    }
    telemetry = {
        "elapsed_ms": 95,
        "peak_sd_cli_rss_kb": 8_000_000,
        "minimum_mem_available_kb": 18_000_000,
    }
    result = {
        "request_id": request_id,
        "status": "succeeded",
        "artifact": artifact,
        "profile": "demo",
        "seed": CANONICAL_SEED,
        "exit_code": 0,
        "elapsed_ms": telemetry["elapsed_ms"],
    }

    (root / "metadata/preflight.sanitized.json").write_text(json.dumps(preflight))
    (root / "metadata/local-acceptance.json").write_text(json.dumps(local))
    (root / "metadata/real-generation-count.json").write_text(json.dumps({"canonical_real_acceptance_starts": 1}))
    (root / "metadata/server-stop.json").write_text(json.dumps({"server_stop_pass": True, "no_orphan_sd_cli_pass": True}))
    (run_dir / "request.json").write_text(json.dumps(request))
    (run_dir / "stdout.log").write_text("sd-cli completed\n")
    (run_dir / "stderr.log").write_text("")
    (run_dir / "telemetry.json").write_text(json.dumps(telemetry))
    (run_dir / "result.json").write_text(json.dumps(result))

    contract = baseline_contract_snapshot()
    contract["real_acceptance_starts"] = 1
    contract["acceptance_artifact_sha256"] = artifact["sha256"]
    contract["fetched_artifact_sha256"] = artifact["sha256"]
    contract["server_stop_pass"] = True
    contract["evidence_completed"] = True
    contract["overall_pass"] = True
    contract["evidence_files"] = [
        "metadata/preflight.sanitized.json",
        "metadata/local-acceptance.json",
        "metadata/real-generation-count.json",
        "metadata/server-stop.json",
        "artifacts/release-acceptance-512.png",
        f"runs/{request_id}/request.json",
        f"runs/{request_id}/stdout.log",
        f"runs/{request_id}/stderr.log",
        f"runs/{request_id}/telemetry.json",
        f"runs/{request_id}/result.json",
    ]
    contract["manifest_paths"] = list(contract["evidence_files"])
    (root / "metadata/contract.json").write_text(json.dumps(contract))
    ((root / "RELEASE-REPORT.json")).write_text(json.dumps({"status": "PASS", "CORE_LOCAL_DEMO": "PASS", "EVIDENCE_COLLECTION": "PASS"}))
    rebuild_manifests(root)
    return request_id


class EvidenceSemanticTests(unittest.TestCase):
    def test_realistic_actual_evidence_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            build_realistic_evidence(root)
            self.assertEqual(verify(root)["status"], "PASS")

    def test_mutated_runtime_device_or_bind_fails(self):
        cases = [
            ("runtime_devices_output", "CPU\nCUDA0"),
            ("host", "0.0.0.0"),
            ("port", 9999),
            ("mem_available_kb", 1),
            ("disk_free_bytes", 1),
        ]
        for key, value in cases:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                build_realistic_evidence(root)
                p = root / "metadata/preflight.sanitized.json"
                doc = json.loads(p.read_text())
                doc[key] = value
                p.write_text(json.dumps(doc))
                rebuild_manifests(root)
                with self.assertRaises(EvidenceError):
                    verify(root)

    def test_mutated_preflight_hash_fails_even_with_valid_contract(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            build_realistic_evidence(root)
            p = root / "metadata/preflight.sanitized.json"
            doc = json.loads(p.read_text())
            doc["inputs"]["dit"]["sha256"] = "0" * 64
            p.write_text(json.dumps(doc))
            rebuild_manifests(root)
            with self.assertRaises(EvidenceError):
                verify(root)

    def test_mutated_preflight_variation_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            build_realistic_evidence(root)
            p = root / "metadata/preflight.sanitized.json"
            doc = json.loads(p.read_text())
            doc["inputs"]["vae"]["variation"] = "pytorch/default"
            p.write_text(json.dumps(doc))
            rebuild_manifests(root)
            with self.assertRaises(EvidenceError):
                verify(root)

    def test_mutated_local_recipe_fails(self):
        cases = [("prompt", "wrong prompt"), ("seed", 7), ("profile", "balanced")]
        for key, value in cases:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                build_realistic_evidence(root)
                p = root / "metadata/local-acceptance.json"
                doc = json.loads(p.read_text())
                doc[key] = value
                p.write_text(json.dumps(doc))
                rebuild_manifests(root)
                with self.assertRaises(EvidenceError):
                    verify(root)

    def test_missing_or_inconsistent_run_evidence_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            request_id = build_realistic_evidence(root)
            (root / "runs" / request_id / "telemetry.json").unlink()
            rebuild_manifests(root)
            with self.assertRaises(EvidenceError):
                verify(root)

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            request_id = build_realistic_evidence(root)
            p = root / "runs" / request_id / "result.json"
            doc = json.loads(p.read_text())
            doc["profile"] = "balanced"
            p.write_text(json.dumps(doc))
            rebuild_manifests(root)
            with self.assertRaises(EvidenceError):
                verify(root)

    def test_run_result_seed_exit_and_elapsed_must_match(self):
        mutations = [
            ("seed", 7),
            ("exit_code", 1),
            ("elapsed_ms", 999),
        ]
        for key, value in mutations:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                request_id = build_realistic_evidence(root)
                p = root / "runs" / request_id / "result.json"
                doc = json.loads(p.read_text())
                doc[key] = value
                p.write_text(json.dumps(doc))
                rebuild_manifests(root)
                with self.assertRaises(EvidenceError):
                    verify(root)

    def test_artifact_metadata_must_match_actual_png(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            build_realistic_evidence(root)
            p = root / "metadata/local-acceptance.json"
            doc = json.loads(p.read_text())
            doc["artifact"]["width"] = 640
            p.write_text(json.dumps(doc))
            rebuild_manifests(root)
            with self.assertRaises(EvidenceError):
                verify(root)


if __name__ == "__main__":
    unittest.main()
