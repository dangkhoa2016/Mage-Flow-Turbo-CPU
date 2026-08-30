import unittest
from app.resources import required_resources
from scripts.kaggle.preflight import mem_available_kb
class ResourceGateTests(unittest.TestCase):
    def test_linux_mem_available_is_parseable_when_present(self):
        value=mem_available_kb()
        if value is not None:self.assertGreater(value,0)
    def test_profile_thresholds_are_frozen(self):
        mem,disk=required_resources('demo'); self.assertEqual(mem,16*1024*1024); self.assertEqual(disk,2*1024**3)
        mem,disk=required_resources('balanced'); self.assertEqual(mem,16*1024*1024); self.assertEqual(disk,2*1024**3)
        mem,disk=required_resources('research'); self.assertEqual(mem,20*1024*1024); self.assertEqual(disk,3*1024**3)
if __name__=='__main__':unittest.main()
