from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "scripts" / "kaggle" / "bootstrap-cpu-demo.sh"
PORTABLE_BUILDER = ROOT / "scripts" / "kaggle" / "build-portable-sd-cli.sh"
PORTABLE_WORKFLOW = ROOT / ".github" / "workflows" / "portable-runtime.yml"
GENERIC_ARCHIVE_NAME = "stable-diffusion-cpp-6b3edaa-portable-cpu-runtime.tar.gz"
LEGACY_ARCHIVE_NAME = "mage-flow-turbo-sd-cli-linux-x86_64-6b3edaa.tar.gz"


class RuntimeBootstrapContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = BOOTSTRAP.read_text(encoding="utf-8")

    def test_source_build_targets_sd_cli_only(self):
        self.assertIn('--target sd-cli', self.text)
        self.assertNotIn('Built target sd-server', self.text)

    def test_runtime_mode_supports_auto_prebuilt_and_source(self):
        self.assertIn('MAGE_RUNTIME_MODE', self.text)
        self.assertIn('auto', self.text)
        self.assertIn('prebuilt', self.text)
        self.assertIn('source', self.text)

    def test_prebuilt_runtime_is_fail_closed_before_reuse(self):
        self.assertIn('MAGE_PREBUILT_SD_CLI', self.text)
        self.assertIn('MAGE_PREBUILT_SD_CLI_SHA256', self.text)
        self.assertIn('sha256sum -c', self.text)
        self.assertIn('verify_binary', self.text)

    def test_auto_mode_can_fallback_to_source_build(self):
        self.assertIn('RELEASE_PREBUILT_FALLBACK=SOURCE', self.text)
        self.assertIn('RELEASE_RUNTIME_SOURCE_BUILD=PASS', self.text)

    def test_compiler_noise_goes_to_bootstrap_log_not_notebook_stdout(self):
        self.assertNotIn('exec > >(tee -a "$ROOT/logs/bootstrap.log") 2>&1', self.text)
        self.assertIn('BOOTSTRAP_LOG="$ROOT/logs/bootstrap.log"', self.text)
        self.assertIn('tail -n', self.text)

    def test_portable_builder_disables_native_cpu_and_builds_sd_cli_only(self):
        text = PORTABLE_BUILDER.read_text(encoding="utf-8")
        self.assertIn('-DGGML_NATIVE=OFF', text)
        self.assertIn('--target sd-cli', text)
        self.assertIn('runtime-manifest.json', text)
        self.assertIn('SHA256SUMS', text)

    def test_portable_archive_uses_generic_stable_diffusion_cpp_name(self):
        text = PORTABLE_BUILDER.read_text(encoding="utf-8")
        self.assertIn(f'ARCHIVE_NAME="{GENERIC_ARCHIVE_NAME}"', text)
        self.assertNotIn(LEGACY_ARCHIVE_NAME, text)

    def test_portable_archive_sidecar_uses_relative_filename(self):
        text = PORTABLE_BUILDER.read_text(encoding="utf-8")
        self.assertIn('ARCHIVE_NAME=', text)
        self.assertIn('cd "$ROOT"', text)
        self.assertIn('sha256sum "$ARCHIVE_NAME" > "$ARCHIVE_NAME.sha256"', text)
        self.assertNotIn('sha256sum "$ROOT/', text)

    def test_workflow_uses_generic_artifact_name_and_verifies_in_archive_directory(self):
        text = PORTABLE_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('cd .portable-sd-cli-build', text)
        self.assertIn(f'sha256sum -c {GENERIC_ARCHIVE_NAME}.sha256', text)
        self.assertIn(f'name: stable-diffusion-cpp-6b3edaa-portable-cpu-runtime', text)
        self.assertNotIn(LEGACY_ARCHIVE_NAME, text)


if __name__ == "__main__":
    unittest.main()
