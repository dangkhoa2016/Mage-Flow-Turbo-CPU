import hashlib
import tempfile
import unittest
from pathlib import Path
from app.inputs import resolve_exact_input, InputResolutionError

class InputResolverTests(unittest.TestCase):
    def test_resolves_version_agnostic_vae_only(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)/'models/dangkhoa2016/mage-flow-community-mage-flow-turbo/pytorch/vae-only/7/diffusion_pytorch_model.safetensors'
            p.parent.mkdir(parents=True); p.write_bytes(b'vae-test')
            sha=hashlib.sha256(b'vae-test').hexdigest()
            got=resolve_exact_input(Path(td), filename=p.name, required_fragment='mage-flow-community-mage-flow-turbo/pytorch/vae-only', forbidden_fragment='/pytorch/default/', expected_size=8, expected_sha256=sha)
            self.assertEqual(got.path, p.resolve())

    def test_never_falls_back_to_pytorch_default(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)/'models/dangkhoa2016/mage-flow-community-mage-flow-turbo/pytorch/default/1/vae/diffusion_pytorch_model.safetensors'
            p.parent.mkdir(parents=True); p.write_bytes(b'vae-test')
            with self.assertRaises(InputResolutionError):
                resolve_exact_input(Path(td), filename=p.name, required_fragment='mage-flow-community-mage-flow-turbo/pytorch/vae-only', forbidden_fragment='/pytorch/default/', expected_size=8, expected_sha256=hashlib.sha256(b'vae-test').hexdigest())

    def test_multiple_candidates_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            for v in ('1','2'):
                p=Path(td)/f'm/mage-flow-community-mage-flow-turbo/pytorch/vae-only/{v}/diffusion_pytorch_model.safetensors'
                p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b'vae-test')
            with self.assertRaises(InputResolutionError):
                resolve_exact_input(Path(td), filename='diffusion_pytorch_model.safetensors', required_fragment='mage-flow-community-mage-flow-turbo/pytorch/vae-only', forbidden_fragment='/pytorch/default/', expected_size=8, expected_sha256=hashlib.sha256(b'vae-test').hexdigest())

if __name__=='__main__': unittest.main()
