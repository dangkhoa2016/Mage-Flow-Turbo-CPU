import json
import tempfile
import unittest
from pathlib import Path

from app.backend import generate
from app.config import ServiceConfig
from app.profiles import load_profile


class BackendRunEvidenceTests(unittest.TestCase):
    def test_result_and_telemetry_are_crosscheckable(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); out=root/'outputs'; runs=root/'runs'; out.mkdir(); runs.mkdir()
            cfg=ServiceConfig('/unused/sd-cli','/unused/dit.gguf','/unused/qwen.gguf','/unused/vae.safetensors',str(out),str(runs))
            result=generate(cfg,prompt='hello',seed=42,profile=load_profile('demo'),client_request_id='req-1',fake=True)
            run=runs/'req-1'
            stored=json.loads((run/'result.json').read_text())
            telemetry=json.loads((run/'telemetry.json').read_text())
            self.assertEqual(stored['request_id'],'req-1')
            self.assertEqual(stored['seed'],42)
            self.assertEqual(stored['exit_code'],0)
            self.assertEqual(stored['elapsed_ms'],telemetry['elapsed_ms'])
            self.assertEqual(stored['profile'],'demo')
            self.assertEqual(stored['artifact']['sha256'],result.artifact['sha256'])


if __name__=='__main__': unittest.main()
