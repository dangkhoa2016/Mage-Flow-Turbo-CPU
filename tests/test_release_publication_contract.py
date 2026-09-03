import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE_NOTES = ROOT / "docs" / "RELEASE-NOTES-v1.0.0.md"
RELEASE_NOTES_VI = ROOT / "docs" / "RELEASE-NOTES-v1.0.0.vi.md"

RUNTIME_DATASET = "dangkhoa2016/stable-diffusion-cpp-6b3edaa-portable-cpu-runtime"
SD_CLI_SHA = "7539d90b99eaf2b6279eec4f9006a68ae53e87bfe0c9c325ff3f329220468a5c"


class ReleasePublicationContractTests(unittest.TestCase):
    def test_release_notes_are_bilingual_and_complete(self):
        for path in (RELEASE_NOTES, RELEASE_NOTES_VI):
            self.assertTrue(path.is_file(), f"{path.name} missing")
            text = path.read_text(encoding="utf-8")
            self.assertIn("Language / Ngôn ngữ", text)
            self.assertIn("v1.0.0", text)

    def test_release_notes_pin_frozen_technical_contract(self):
        text = RELEASE_NOTES.read_text(encoding="utf-8")
        for token in (
            "6b3edaaf32cc19e5bb2d819c788bd557eddc8eba",
            "4c3dafc143ee64121692b6b63563a4f5288bf6183c4870e1d65f1566519ba7f0",
            "66358cb18bb6b3b1b6675aa412c7a88ef01d228f481184d13668e5201c730a0a",
            "34e076dc1e8a15321e1e07be5111d59cf16dd10b804b7c7e20b4de29013427e0",
            "pytorch/vae-only",
        ):
            self.assertIn(token, text)

    def test_release_notes_pin_public_runtime_dataset(self):
        text = RELEASE_NOTES.read_text(encoding="utf-8")
        self.assertIn(RUNTIME_DATASET, text)
        self.assertIn(SD_CLI_SHA, text)

    def test_license_gate_requires_owner_selected_mit_license(self):
        license_file = ROOT / "LICENSE"
        self.assertTrue(license_file.is_file(), "LICENSE file is required")
        lic = license_file.read_text(encoding="utf-8")
        self.assertIn("MIT License", lic)
        self.assertIn("Đăng Khoa", lic)
        self.assertIn("i.am@dangkhoa.dev", lic)

    def test_release_notes_pin_single_qualified_release_tree(self):
        text = RELEASE_NOTES.read_text(encoding="utf-8")
        self.assertIn("2026-09-04", text)
        self.assertIn("final qualified source tree", text)
        self.assertIn("main", text)
        self.assertIn("`v1.0.0`", text)


if __name__ == "__main__":
    unittest.main()
