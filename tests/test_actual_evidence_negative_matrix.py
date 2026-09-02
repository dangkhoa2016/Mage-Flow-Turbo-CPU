import json
import tempfile
import unittest
from pathlib import Path

from scripts.verify_evidence import EvidenceError, verify
from tests.test_evidence_semantics import build_realistic_evidence, rebuild_manifests


def mutate_json(root: Path, rel: str, fn) -> None:
    p=root/rel; doc=json.loads(p.read_text()); fn(doc); p.write_text(json.dumps(doc))


class ActualEvidenceNegativeMatrixTests(unittest.TestCase):
    def test_16_actual_evidence_mutations_are_expected_failures(self):
        cases=[
            ('1 preflight dit hash', lambda r,q: mutate_json(r,'metadata/preflight.sanitized.json',lambda d:d['inputs']['dit'].__setitem__('sha256','0'*64))),
            ('2 preflight vae variation', lambda r,q: mutate_json(r,'metadata/preflight.sanitized.json',lambda d:d['inputs']['vae'].__setitem__('variation','pytorch/default'))),
            ('3 actual runtime version', lambda r,q: mutate_json(r,'metadata/preflight.sanitized.json',lambda d:d.__setitem__('runtime_version_output','stable-diffusion.cpp wrong'))),
            ('4 accelerator device appears', lambda r,q: mutate_json(r,'metadata/preflight.sanitized.json',lambda d:d.__setitem__('runtime_devices_output','CPU\nCUDA0'))),
            ('5 backend bind changed', lambda r,q: mutate_json(r,'metadata/preflight.sanitized.json',lambda d:d.__setitem__('host','0.0.0.0'))),
            ('6 canonical prompt', lambda r,q: mutate_json(r,'metadata/local-acceptance.json',lambda d:d.__setitem__('prompt','wrong'))),
            ('7 canonical seed', lambda r,q: mutate_json(r,'metadata/local-acceptance.json',lambda d:d.__setitem__('seed',7))),
            ('8 canonical profile', lambda r,q: mutate_json(r,'metadata/local-acceptance.json',lambda d:d.__setitem__('profile','balanced'))),
            ('9 exactly one real start', lambda r,q: mutate_json(r,'metadata/real-generation-count.json',lambda d:d.__setitem__('canonical_real_acceptance_starts',2))),
            ('10 clean server stop', lambda r,q: mutate_json(r,'metadata/server-stop.json',lambda d:d.__setitem__('server_stop_pass',False))),
            ('11 artifact metadata width', lambda r,q: mutate_json(r,'metadata/local-acceptance.json',lambda d:d['artifact'].__setitem__('width',640))),
            ('12 run result profile', lambda r,q: mutate_json(r,f'runs/{q}/result.json',lambda d:d.__setitem__('profile','balanced'))),
            ('13 run result seed', lambda r,q: mutate_json(r,f'runs/{q}/result.json',lambda d:d.__setitem__('seed',9))),
            ('14 run result exit', lambda r,q: mutate_json(r,f'runs/{q}/result.json',lambda d:d.__setitem__('exit_code',1))),
            ('15 run result elapsed', lambda r,q: mutate_json(r,f'runs/{q}/result.json',lambda d:d.__setitem__('elapsed_ms',999))),
            ('16 run telemetry missing', lambda r,q: (r/'runs'/q/'telemetry.json').unlink()),
        ]
        self.assertEqual(len(cases),16)
        for name,mutator in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as td:
                root=Path(td); request_id=build_realistic_evidence(root); mutator(root,request_id); rebuild_manifests(root)
                with self.assertRaises(EvidenceError): verify(root)


if __name__=='__main__': unittest.main()
