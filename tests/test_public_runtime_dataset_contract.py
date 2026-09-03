from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROD = ROOT / "notebooks/kaggle-cpu-production-demo.ipynb"


def decoded_source(path: Path):
    nb = json.loads(path.read_text(encoding="utf-8"))
    return "\n".join("".join(c.get("source", [])) for c in nb.get("cells", []))


class PublicRuntimeDatasetContractTests(unittest.TestCase):
    def test_public_notebook_prefers_verified_prebuilt_with_auto_fallback(self):
        src = decoded_source(PROD)
        self.assertIn(
            "/kaggle/input/datasets/dangkhoa2016/stable-diffusion-cpp-6b3edaa-portable-cpu-runtime",
            src,
        )
        self.assertIn('os.environ["MAGE_RUNTIME_MODE"] = "auto"', src)
        self.assertIn("PUBLIC_RUNTIME_PREBUILT_HINT=PASS", src)
        self.assertIn("PUBLIC_RUNTIME_PREBUILT_HINT=NOT_ATTACHED_SOURCE_FALLBACK_AVAILABLE", src)
        self.assertIn("7539d90b99eaf2b6279eec4f9006a68ae53e87bfe0c9c325ff3f329220468a5c", src)

    def test_notebook_is_valid_json(self):
        json.loads(PROD.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
