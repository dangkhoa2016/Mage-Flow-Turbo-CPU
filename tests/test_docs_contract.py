import unittest
from pathlib import Path
PAIRS=[('README.md','README.vi.md'),('docs/production-demo.md','docs/production-demo.vi.md'),('docs/kaggle-production-demo-notebook.md','docs/kaggle-production-demo-notebook.vi.md'),('docs/TESTING.md','docs/TESTING.vi.md'),('docs/TROUBLESHOOTING.md','docs/TROUBLESHOOTING.vi.md'),('CHANGELOG.md','CHANGELOG.vi.md')]
TOKENS=['6b3edaaf32cc19e5bb2d819c788bd557eddc8eba','4c3dafc143ee64121692b6b63563a4f5288bf6183c4870e1d65f1566519ba7f0','66358cb18bb6b3b1b6675aa412c7a88ef01d228f481184d13668e5201c730a0a','34e076dc1e8a15321e1e07be5111d59cf16dd10b804b7c7e20b4de29013427e0','pytorch/vae-only','512','640','1024']
class DocsContractTests(unittest.TestCase):
    def test_pairs_and_frozen_tokens(self):
        for en,vi in PAIRS:
            with self.subTest(pair=(en,vi)):
                et=Path(en).read_text(encoding='utf-8'); vt=Path(vi).read_text(encoding='utf-8')
                self.assertIn('Language / Ngôn ngữ',et); self.assertIn('Language / Ngôn ngữ',vt)
                for t in TOKENS:
                    self.assertIn(t,et); self.assertIn(t,vt)
    def test_no_default_vae_dependency_claim(self):
        for en,vi in PAIRS:
            for p in (en,vi):
                text=Path(p).read_text(encoding='utf-8').lower()
                self.assertNotIn('attach pytorch/default',text)

if __name__=='__main__': unittest.main()
