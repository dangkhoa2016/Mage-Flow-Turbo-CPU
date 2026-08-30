import unittest
from app.profiles import load_profile
class ProfileTests(unittest.TestCase):
    def test_demo_profile_is_512_default(self):
        p=load_profile('demo'); self.assertEqual((p.width,p.height),(512,512));self.assertEqual(p.steps,4);self.assertEqual(p.cfg_scale,1.0);self.assertEqual(p.threads,4);self.assertEqual(p.timeout_seconds,900)
    def test_balanced_and_research_profiles(self):
        b=load_profile('balanced');r=load_profile('research');self.assertEqual((b.width,b.height,b.timeout_seconds),(640,640,1200));self.assertEqual((r.width,r.height,r.timeout_seconds),(1024,1024,2700))
    def test_768_is_not_primary_profile(self):
        with self.assertRaises(ValueError):load_profile('768')
if __name__=='__main__':unittest.main()
