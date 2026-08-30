import unittest
from app.config import validate_generation_payload

class UnicodePromptTests(unittest.TestCase):
    def test_vietnamese_utf8_survives_validation(self):
        prompt='Một con cáo đỏ nhỏ ngồi trong khu rừng xanh yên tĩnh, ánh sáng tự nhiên.'
        self.assertEqual(validate_generation_payload({'prompt':prompt,'seed':42})['prompt'], prompt)

if __name__ == '__main__': unittest.main()
