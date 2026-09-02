import json
import tempfile
import unittest
from pathlib import Path

from scripts.kaggle.collect_evidence import copy_canonical_run_evidence, sanitize_preflight_inputs


class EvidenceCollectorTests(unittest.TestCase):
    def test_sanitized_input_identity_preserves_variation_without_absolute_path(self):
        preflight_inputs = {
            "dit": {"path": "/kaggle/input/models/dangkhoa2016/mage-flow-community-mage-flow-turbo/gguf/q8-0/1/Mage-Flow-Turbo-DiT-Q8_0.gguf", "bytes": 4381806208, "sha256": "4c3dafc143ee64121692b6b63563a4f5288bf6183c4870e1d65f1566519ba7f0"},
            "qwen": {"path": "/kaggle/input/models/dangkhoa2016/qwen-qwen3-vl-4b-instruct-gguf/gguf/q4-k-m/1/Qwen3VL-4B-Instruct-Q4_K_M.gguf", "bytes": 123, "sha256": "66358cb18bb6b3b1b6675aa412c7a88ef01d228f481184d13668e5201c730a0a"},
            "vae": {"path": "/kaggle/input/models/dangkhoa2016/mage-flow-community-mage-flow-turbo/pytorch/vae-only/7/diffusion_pytorch_model.safetensors", "bytes": 345053056, "sha256": "34e076dc1e8a15321e1e07be5111d59cf16dd10b804b7c7e20b4de29013427e0"},
        }
        sanitized = sanitize_preflight_inputs(preflight_inputs)
        self.assertEqual(sanitized["dit"]["variation"], "gguf/q8-0")
        self.assertEqual(sanitized["qwen"]["variation"], "gguf/q4-k-m")
        self.assertEqual(sanitized["vae"]["variation"], "pytorch/vae-only")
        self.assertNotIn("path", sanitized["vae"])

    def test_sanitized_input_identity_rejects_legacy_vae_path(self):
        preflight_inputs = {
            "dit": {"path": "/x/mage-flow-community-mage-flow-turbo/gguf/q8-0/1/Mage-Flow-Turbo-DiT-Q8_0.gguf", "bytes": 1, "sha256": "a"},
            "qwen": {"path": "/x/qwen-qwen3-vl-4b-instruct-gguf/gguf/q4-k-m/1/Qwen3VL-4B-Instruct-Q4_K_M.gguf", "bytes": 1, "sha256": "b"},
            "vae": {"path": "/x/mage-flow-community-mage-flow-turbo/pytorch/default/1/vae/diffusion_pytorch_model.safetensors", "bytes": 1, "sha256": "c"},
        }
        with self.assertRaises(ValueError):
            sanitize_preflight_inputs(preflight_inputs)

    def test_copies_sanitized_canonical_run_evidence_and_excludes_argv(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runtime = root / "runtime"
            stage = root / "stage"
            request_id = "release-acceptance-123"
            run = runtime / "runs" / request_id
            run.mkdir(parents=True)
            stage.mkdir()
            (run / "request.json").write_text(json.dumps({"prompt": "p", "seed": 42, "profile": "demo", "client_request_id": request_id}))
            (run / "stdout.log").write_text("stdout\n")
            (run / "stderr.log").write_text("stderr\n")
            (run / "telemetry.json").write_text(json.dumps({"elapsed_ms": 1, "peak_sd_cli_rss_kb": 2, "minimum_mem_available_kb": 3}))
            (run / "result.json").write_text(json.dumps({"request_id": request_id, "status": "succeeded", "profile": "demo", "artifact": {"sha256": "a" * 64}}))
            (run / "argv.json").write_text(json.dumps(["sd-cli", "--diffusion-model", "/absolute/model.gguf"]))

            copied = copy_canonical_run_evidence(runtime, stage, request_id)

            expected = {
                f"runs/{request_id}/request.json",
                f"runs/{request_id}/stdout.log",
                f"runs/{request_id}/stderr.log",
                f"runs/{request_id}/telemetry.json",
                f"runs/{request_id}/result.json",
            }
            self.assertEqual(set(copied), expected)
            for rel in expected:
                self.assertTrue((stage / rel).is_file(), rel)
            self.assertFalse((stage / "runs" / request_id / "argv.json").exists())

    def test_rejects_unsafe_request_id_or_missing_file(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runtime = root / "runtime"
            stage = root / "stage"
            stage.mkdir()
            with self.assertRaises(ValueError):
                copy_canonical_run_evidence(runtime, stage, "../escape")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runtime = root / "runtime"
            stage = root / "stage"
            request_id = "release-acceptance-123"
            (runtime / "runs" / request_id).mkdir(parents=True)
            stage.mkdir()
            with self.assertRaises(FileNotFoundError):
                copy_canonical_run_evidence(runtime, stage, request_id)


if __name__ == "__main__":
    unittest.main()

class FullEvidenceCollectorTests(unittest.TestCase):
    def test_full_collector_archives_run_evidence_without_argv(self):
        import sys
        import tarfile
        from unittest.mock import patch
        from app.artifacts import inspect_png, write_fake_rgb_png
        from app.constants import CANONICAL_PROMPT, CANONICAL_SEED, DIT_BYTES, DIT_FILENAME, DIT_SHA256, QWEN_FILENAME, QWEN_SHA256, SDCPP_COMMIT, SDCPP_SHORT, VAE_BYTES, VAE_FILENAME, VAE_SHA256
        from scripts.kaggle.collect_evidence import main

        with tempfile.TemporaryDirectory() as td:
            rr=Path(td)/'runtime'; state=rr/'state'; ev=rr/'evidence'; run_id='release-acceptance-123'; run=rr/'runs'/run_id
            for d in (state,ev,run,rr/'logs'): d.mkdir(parents=True,exist_ok=True)
            png=ev/'release-acceptance-512.png'; write_fake_rgb_png(png,512,512); artifact=inspect_png(png,512,512)
            pre={
                'status':'PASS','source_git_head':'f'*40,'source_git_clean':True,
                'runtime_commit_expected':SDCPP_COMMIT,'runtime_version_output':f'stable-diffusion.cpp {SDCPP_SHORT}',
                'runtime_devices_output':'CPU','host':'127.0.0.1','port':8090,
                'mem_available_kb':20*1024*1024,'min_mem_available_kb':16*1024*1024,
                'disk_free_bytes':4*1024**3,'min_disk_free_bytes':2*1024**3,
                'gates':{k:'PASS' for k in ('RELEASE_SOURCE_GIT_PROVENANCE','RELEASE_CPU_ONLY_POLICY','RELEASE_MODEL_IDENTITIES','RELEASE_SD_CLI_PRESENT','RELEASE_RUNTIME_COMMIT','RELEASE_RUNTIME_CPU_ONLY','RELEASE_MEMORY_GATE','RELEASE_DISK_GATE','RELEASE_RUNTIME_DIRS_WRITABLE','RELEASE_LOCAL_PORT_AVAILABLE','RELEASE_SOURCE_NO_MODEL_WEIGHTS')},
                'inputs':{
                    'dit':{'path':f'/kaggle/input/models/dangkhoa2016/mage-flow-community-mage-flow-turbo/gguf/q8-0/1/{DIT_FILENAME}','bytes':DIT_BYTES,'sha256':DIT_SHA256},
                    'qwen':{'path':f'/kaggle/input/models/dangkhoa2016/qwen-qwen3-vl-4b-instruct-gguf/gguf/q4-k-m/1/{QWEN_FILENAME}','bytes':123,'sha256':QWEN_SHA256},
                    'vae':{'path':f'/kaggle/input/models/dangkhoa2016/mage-flow-community-mage-flow-turbo/pytorch/vae-only/9/{VAE_FILENAME}','bytes':VAE_BYTES,'sha256':VAE_SHA256},
                },
            }
            local={'schema_version':1,'mode':'REAL','status':'PASS','profile':'demo','prompt':CANONICAL_PROMPT,'seed':CANONICAL_SEED,'http_elapsed_ms':100,'request_id':run_id,'artifact':artifact,'artifact_url_path':f'/v1/artifacts/{run_id}.png','public_tunnel_enabled':False}
            (state/'preflight.json').write_text(json.dumps(pre)); (state/'local-acceptance.json').write_text(json.dumps(local)); (state/'real-generation-count.json').write_text(json.dumps({'canonical_real_acceptance_starts':1})); (state/'server-stop.json').write_text(json.dumps({'server_stop_pass':True,'no_orphan_sd_cli_pass':True}))
            (run/'request.json').write_text(json.dumps({'prompt':CANONICAL_PROMPT,'seed':CANONICAL_SEED,'client_request_id':run_id,'profile':'demo'}))
            (run/'stdout.log').write_text('real stdout\n'); (run/'stderr.log').write_text(''); (run/'telemetry.json').write_text(json.dumps({'elapsed_ms':95,'peak_sd_cli_rss_kb':8000000,'minimum_mem_available_kb':18000000})); (run/'result.json').write_text(json.dumps({'request_id':run_id,'status':'succeeded','profile':'demo','seed':42,'exit_code':0,'elapsed_ms':95,'artifact':artifact})); (run/'argv.json').write_text('["sd-cli","/absolute/model.gguf"]')
            with patch.object(sys,'argv',['collect_evidence.py','--runtime-root',str(rr)]):
                self.assertEqual(main(),0)
            archives=sorted(rr.glob('mage-flow-turbo-cpu-production-demo-evidence-*.tar.gz'))
            self.assertEqual(len(archives),1)
            with tarfile.open(archives[0],'r:gz') as tf:
                names=set(tf.getnames())
                sanitized=json.loads(tf.extractfile('metadata/preflight.sanitized.json').read().decode('utf-8'))
            prefix=f'runs/{run_id}/'
            for name in ('request.json','stdout.log','stderr.log','telemetry.json','result.json'):
                self.assertIn(prefix+name,names)
            self.assertNotIn(prefix+'argv.json',names)
            self.assertEqual(sanitized['source_git_head'],'f'*40)
            self.assertIs(sanitized['source_git_clean'],True)
