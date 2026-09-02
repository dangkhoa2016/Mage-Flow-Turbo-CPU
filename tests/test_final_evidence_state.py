import tempfile
import unittest
from pathlib import Path

from scripts.verify_evidence import EvidenceError, verify
from tests.test_evidence_semantics import build_realistic_evidence, rebuild_manifests


class FinalEvidenceStateTests(unittest.TestCase):
    def test_synthetic_valid_evidence_fixture_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            build_realistic_evidence(root)
            self.assertEqual(verify(root)["status"], "PASS")

    def test_manifest_json_is_required(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            build_realistic_evidence(root)
            (root / "MANIFEST.json").unlink()
            # Do not rebuild: this test specifically proves MANIFEST.json is mandatory.
            with self.assertRaises(EvidenceError):
                verify(root)

    def test_manifest_cannot_hide_semantic_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            build_realistic_evidence(root)
            p = root / "metadata/real-generation-count.json"
            p.write_text('{"canonical_real_acceptance_starts": 2}')
            rebuild_manifests(root)
            with self.assertRaises(EvidenceError):
                verify(root)


if __name__ == "__main__":
    unittest.main()
