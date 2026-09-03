import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / 'notebooks' / 'kaggle-cpu-production-demo.ipynb'


def load_bootstrap_cell():
    nb = json.loads(NB.read_text(encoding='utf-8'))
    matches = []
    for cell in nb['cells']:
        if cell.get('cell_type') != 'code':
            continue
        source = ''.join(cell.get('source', []))
        if 'REPO_URL =' in source and "print('SOURCE_HEAD=', SOURCE_HEAD)" in source:
            matches.append(source)
    if len(matches) != 1:
        raise AssertionError(f'expected exactly one source bootstrap cell, found {len(matches)}')
    return nb, matches[0]


class SourceBootstrapContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb, cls.code = load_bootstrap_cell()

    def test_uses_canonical_public_dot_git_url(self):
        self.assertIn(
            'REPO_URL = "https://github.com/dangkhoa2016/Mage-Flow-Turbo-CPU.git"',
            self.code,
        )

    def test_disables_interactive_auth_and_strips_auth_environment(self):
        self.assertIn('git_env = os.environ.copy()', self.code)
        for key in ('GIT_ASKPASS', 'SSH_ASKPASS', 'GH_TOKEN', 'GITHUB_TOKEN'):
            self.assertIn(repr(key), self.code)
        self.assertIn('git_env.pop(key, None)', self.code)
        self.assertIn("git_env['GIT_TERMINAL_PROMPT'] = '0'", self.code)

    def test_ignores_global_and_system_git_config_for_public_clone(self):
        self.assertIn("git_env['GIT_CONFIG_GLOBAL'] = os.devnull", self.code)
        self.assertIn("git_env['GIT_CONFIG_NOSYSTEM'] = '1'", self.code)
        self.assertIn("key == 'GIT_CONFIG_COUNT'", self.code)
        self.assertIn("key.startswith('GIT_CONFIG_KEY_')", self.code)
        self.assertIn("key.startswith('GIT_CONFIG_VALUE_')", self.code)
        self.assertIn("'credential.helper='", self.code)
        self.assertIn("'http.extraHeader='", self.code)

    def test_clones_to_temporary_checkout_before_replacing_final_checkout(self):
        self.assertIn("CLONE_TMP = REPO_DIR.with_name(REPO_DIR.name + '.clone-tmp')", self.code)
        self.assertIn('subprocess.run(clone_cmd, check=True, env=git_env)', self.code)
        clone_index = self.code.index('subprocess.run(clone_cmd, check=True, env=git_env)')
        final_delete_index = self.code.index('if REPO_DIR.exists():', clone_index)
        self.assertLess(clone_index, final_delete_index)
        self.assertIn('CLONE_TMP.rename(REPO_DIR)', self.code)

    def test_verifies_candidate_head_and_clean_worktree_before_promotion(self):
        self.assertIn('SOURCE_HEAD_CANDIDATE =', self.code)
        self.assertIn('SOURCE_STATUS_CANDIDATE =', self.code)
        self.assertIn('CLONE_TMP.rename(REPO_DIR)', self.code)
        candidate_head = self.code.index('SOURCE_HEAD_CANDIDATE =')
        candidate_status = self.code.index('SOURCE_STATUS_CANDIDATE =')
        promotion = self.code.index('CLONE_TMP.rename(REPO_DIR)')
        self.assertLess(candidate_head, promotion)
        self.assertLess(candidate_status, promotion)
        self.assertIn("'status','--porcelain'", self.code.replace(' ', ''))

    def test_records_final_source_head_and_keeps_notebook_output_clean(self):
        self.assertIn("print('SOURCE_HEAD=', SOURCE_HEAD)", self.code)
        self.assertIn('SOURCE_HEAD != SOURCE_HEAD_CANDIDATE', self.code)
        for cell in self.nb['cells']:
            if cell.get('cell_type') == 'code':
                self.assertIsNone(cell.get('execution_count'))
                self.assertEqual(cell.get('outputs', []), [])


if __name__ == '__main__':
    unittest.main()
