import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / 'notebooks' / 'kaggle-cpu-production-demo.ipynb'


def load_notebook():
    nb = json.loads(NB.read_text(encoding='utf-8'))
    markdown = '\n'.join(''.join(c.get('source', [])) for c in nb['cells'] if c.get('cell_type') == 'markdown')
    code = '\n'.join(''.join(c.get('source', [])) for c in nb['cells'] if c.get('cell_type') == 'code')
    return nb, markdown, code


class NotebookUXContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb, cls.md, cls.code = load_notebook()

    def test_public_hero_is_user_facing_not_internal_facing(self):
        self.assertIn('# Mage-Flow-Turbo on CPU', self.md)
        self.assertIn('Production-style Kaggle Demo', self.md)
        self.assertNotIn('# Mage-Flow-Turbo (internal)', self.md)

    def test_bilingual_hierarchy_uses_english_primary_and_vietnamese_companion_blocks(self):
        self.assertGreaterEqual(self.md.count('> **Tiếng Việt**'), 8)
        headings = [line for line in self.md.splitlines() if line.startswith('#')]
        self.assertFalse(any(' / ' in line for line in headings), headings)

    def test_required_inputs_are_presented_as_four_input_table(self):
        self.assertIn('4 required Kaggle inputs', self.md)
        for token in ('| Runtime |', '| DiT |', '| VAE |', '| Text encoder |'):
            self.assertIn(token, self.md)
        self.assertNotIn('Ba input canonical cần attach', self.md)

    def test_runtime_expectations_are_explained_before_execution(self):
        self.assertIn('What to expect', self.md)
        self.assertRegex(self.md, r'1\.7\s*s')
        self.assertRegex(self.md, r'395\.956\s*s|~396\s*s')
        self.assertIn('several minutes', self.md.lower())
        self.assertIn('not a GPU-class latency benchmark', self.md)

    def test_public_section_names_follow_user_journey(self):
        for heading in (
            '## 1. Configure the demo',
            '## 5. Start the local API',
            '## 6. Generate the first image',
            '## 7. View the result',
            '## 10. Reproducibility report',
            '## 12. Final summary',
        ):
            self.assertIn(heading, self.md)
        self.assertNotIn('Canonical real 512 acceptance', self.md)

    def test_resolution_status_is_truthful(self):
        self.assertIn('512×512', self.md)
        self.assertIn('Recommended / qualified', self.md)
        self.assertIn('640×640', self.md)
        self.assertIn('Optional', self.md)
        self.assertIn('1024×1024', self.md)
        self.assertIn('Experimental / research', self.md)

    def test_optional_custom_prompt_is_easy_to_find_without_changing_default_run_all(self):
        for token in ('CUSTOM_PROMPT =', 'CUSTOM_SEED =', 'RUN_OPTIONAL_USER_GENERATION = False'):
            self.assertIn(token, self.code)
        self.assertIn("'prompt':CUSTOM_PROMPT", self.code)
        self.assertIn("'seed':CUSTOM_SEED", self.code)

    def test_engineering_contracts_and_machine_markers_are_preserved(self):
        for token in (
            "print('SOURCE_HEAD=', SOURCE_HEAD)",
            'os.environ["MAGE_RUNTIME_MODE"] = "auto"',
            '7539d90b99eaf2b6279eec4f9006a68ae53e87bfe0c9c325ff3f329220468a5c',
            "subprocess.run(['python3','scripts/kaggle/preflight.py'],check=True)",
            "subprocess.run(['python3','scripts/kaggle/local_acceptance.py'],check=True)",
            "subprocess.run(['bash','scripts/kaggle/collect-production-demo-evidence.sh'],check=True)",
            "subprocess.run(['bash','scripts/kaggle/stop-cpu-demo.sh'],check=True)",
            'CORE_LOCAL_DEMO=',
            'EVIDENCE_COLLECTION=',
            'PRODUCTION_ORIENTED_DEMO_NOTEBOOK=',
        ):
            self.assertIn(token, self.code)

    def test_committed_notebook_remains_output_clean(self):
        for cell in self.nb['cells']:
            if cell.get('cell_type') == 'code':
                self.assertIsNone(cell.get('execution_count'))
                self.assertEqual(cell.get('outputs', []), [])


if __name__ == '__main__':
    unittest.main()
