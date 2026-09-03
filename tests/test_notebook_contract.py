import json,os,re,unittest
from pathlib import Path

NB=Path('notebooks/kaggle-cpu-production-demo.ipynb')
class NotebookContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb=json.loads(NB.read_text(encoding='utf-8'))
        cls.text='\n'.join(''.join(c.get('source',[])) for c in cls.nb['cells'])
    def test_committed_notebook_is_output_clean(self):
        for c in self.nb['cells']:
            if c.get('cell_type')=='code':
                self.assertIsNone(c.get('execution_count'))
                self.assertEqual(c.get('outputs',[]),[])
    def test_bilingual_and_safe_defaults(self):
        for token in ('English','Tiếng Việt','RUN_LIVE_DEMO = True','ENABLE_PUBLIC_TUNNEL = False','RUN_OPTIONAL_USER_GENERATION = False','MAGE_PROFILE = "demo"','127.0.0.1:8090','127.0.0.1:8091','Restart Session','Run All'):
            self.assertIn(token,self.text)
    def test_exact_three_input_contract_and_no_default_vae(self):
        for token in ('GGUF / q8-0','PyTorch / vae-only','GGUF / q4-k-m','34e076dc1e8a15321e1e07be5111d59cf16dd10b804b7c7e20b4de29013427e0'):
            self.assertIn(token,self.text)
        self.assertNotIn('/pytorch/default',self.text.lower())
    def test_repo_origin_is_finalized_before_authoritative_acceptance(self):
        marker='__MAGE_REPO_URL__'
        if os.environ.get('MAGE_ALLOW_REPO_PLACEHOLDER')=='1':
            self.assertIn(marker,self.text)
        else:
            self.assertNotIn(marker,self.text,'run scripts/configure_repo_origin.py --apply in the real Git repo before final acceptance')
            self.assertRegex(self.text,r'https://github\.com/[^/\s]+/[^/\s\"\']+')

if __name__=='__main__': unittest.main()
