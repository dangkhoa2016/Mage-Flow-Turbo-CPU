import tempfile,unittest
from pathlib import Path
from scripts.verify_evidence import scan_hygiene, EvidenceError
class PublicationHygieneTests(unittest.TestCase):
    def test_model_weight_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'x.gguf'; p.write_bytes(b'x')
            with self.assertRaises(EvidenceError): scan_hygiene(Path(td))
    def test_bearer_secret_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'log.txt'; p.write_text('Authorization: Bearer abcdefghijklmnopqrstuvwxyz')
            with self.assertRaises(EvidenceError): scan_hygiene(Path(td))

    def test_credential_named_runtime_file_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'session-credential.txt'; p.write_text('synthetic')
            with self.assertRaises(EvidenceError): scan_hygiene(Path(td))

if __name__=='__main__': unittest.main()
