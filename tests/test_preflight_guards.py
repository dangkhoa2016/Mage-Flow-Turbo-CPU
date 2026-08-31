import socket
import tempfile
import unittest
from pathlib import Path
from scripts.kaggle.preflight import port_available, source_weight_files, prove_writable

class PreflightGuardTests(unittest.TestCase):
    def test_port_available_detects_owned_or_unowned_listener(self):
        s=socket.socket(); s.bind(('127.0.0.1',0)); port=s.getsockname()[1]
        self.assertFalse(port_available('127.0.0.1',port))
        s.close()
        self.assertTrue(port_available('127.0.0.1',port))

    def test_source_weight_scan_rejects_model_weight_suffixes(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); (root/'app').mkdir(); (root/'app/x.py').write_text('ok')
            self.assertEqual(source_weight_files(root),[])
            (root/'oops.gguf').write_bytes(b'x')
            self.assertEqual([p.name for p in source_weight_files(root)],['oops.gguf'])

    def test_writable_probe_is_ephemeral(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            self.assertTrue(prove_writable(root))
            self.assertEqual(list(root.iterdir()),[])

if __name__=='__main__': unittest.main()
