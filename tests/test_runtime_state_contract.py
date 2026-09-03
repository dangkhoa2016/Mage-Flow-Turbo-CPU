import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / 'notebooks' / 'kaggle-cpu-production-demo.ipynb'


def load_notebook():
    nb = json.loads(NB.read_text(encoding='utf-8'))
    code_cells = [
        ''.join(cell.get('source', []))
        for cell in nb['cells']
        if cell.get('cell_type') == 'code'
    ]
    config = [
        code for code in code_cells
        if 'RUN_LIVE_DEMO = True' in code and "os.environ['MAGE_RUNTIME_ROOT']" in code
    ]
    if len(config) != 1:
        raise AssertionError(f'expected exactly one runtime config cell, found {len(config)}')
    return nb, code_cells, config[0]


class RuntimeStateContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb, cls.code_cells, cls.config = load_notebook()
        cls.all_code = '\n'.join(cls.code_cells)

    def test_uses_canonical_runtime_root_and_explicit_reset_path_object(self):
        self.assertIn("os.environ['MAGE_RUNTIME_ROOT'] = '/kaggle/working/mage-flow-turbo-runtime'", self.config)
        self.assertIn("runtime_root = Path(os.environ['MAGE_RUNTIME_ROOT'])", self.config)

    def test_stops_public_and_local_services_before_runtime_root_deletion(self):
        pub = "subprocess.run(['bash','scripts/kaggle/stop-authenticated-public-demo.sh'],check=True)"
        local = "subprocess.run(['bash','scripts/kaggle/stop-cpu-demo.sh'],check=True)"
        delete = 'shutil.rmtree(runtime_root)'
        for token in (pub, local, delete):
            self.assertIn(token, self.config)
        self.assertLess(self.config.index(pub), self.config.index(delete))
        self.assertLess(self.config.index(local), self.config.index(delete))

    def test_full_runtime_root_is_removed_to_clear_all_authoritative_run_state(self):
        self.assertIn('if runtime_root.exists():', self.config)
        self.assertIn('shutil.rmtree(runtime_root)', self.config)
        # Do not paper over stale counters with the emergency override.
        self.assertNotIn('MAGE_ALLOW_NEW_ACCEPTANCE', self.config)

    def test_reset_happens_before_environment_capture_and_runtime_bootstrap(self):
        reset_cells = [i for i, code in enumerate(self.code_cells) if 'RELEASE_RUNTIME_STATE_RESET=PASS' in code]
        self.assertEqual(len(reset_cells), 1, reset_cells)
        reset_cell = reset_cells[0]
        capture_cell = next(i for i, code in enumerate(self.code_cells) if 'scripts/kaggle/capture-environment.sh' in code)
        bootstrap_cell = next(i for i, code in enumerate(self.code_cells) if 'scripts/kaggle/bootstrap-cpu-demo.sh' in code)
        self.assertLess(reset_cell, capture_cell)
        self.assertLess(reset_cell, bootstrap_cell)

    def test_emits_machine_readable_reset_marker(self):
        self.assertIn("print('RELEASE_RUNTIME_STATE_RESET=PASS')", self.config)

    def test_preserves_prebuilt_and_single_real_acceptance_contracts(self):
        for token in (
            'os.environ["MAGE_RUNTIME_MODE"] = "auto"',
            '7539d90b99eaf2b6279eec4f9006a68ae53e87bfe0c9c325ff3f329220468a5c',
            "subprocess.run(['python3','scripts/kaggle/local_acceptance.py'],check=True)",
            'RUN_OPTIONAL_USER_GENERATION = False',
        ):
            self.assertIn(token, self.all_code)
        self.assertEqual(self.all_code.count("scripts/kaggle/local_acceptance.py"), 1)

    def test_committed_notebook_remains_output_clean(self):
        for i, cell in enumerate(self.nb['cells']):
            if cell.get('cell_type') == 'code':
                self.assertIsNone(cell.get('execution_count'), i)
                self.assertEqual(cell.get('outputs', []), [], i)


if __name__ == '__main__':
    unittest.main()
