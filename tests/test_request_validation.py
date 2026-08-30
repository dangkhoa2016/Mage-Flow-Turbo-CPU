import unittest
from app.config import validate_generation_payload

class RequestValidationTests(unittest.TestCase):
    def test_valid_payload(self):
        got = validate_generation_payload({
            'prompt': 'A small red fox.', 'seed': 42,
            'client_request_id': 'demo-1', 'profile': 'demo'
        })
        self.assertEqual(got['profile'], 'demo')
        self.assertEqual(got['seed'], 42)

    def test_rejects_arbitrary_resolution_by_default(self):
        with self.assertRaises(ValueError):
            validate_generation_payload({'prompt':'x','seed':1,'width':768,'height':768})

    def test_rejects_unknown_field(self):
        with self.assertRaises(ValueError):
            validate_generation_payload({'prompt':'x','seed':1,'evil':True})

    def test_rejects_bad_prompt_and_seed(self):
        for payload in ({'prompt':'','seed':1},{'prompt':'x','seed':-1},{'prompt':'x','seed':'42'}):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                validate_generation_payload(payload)

if __name__ == '__main__': unittest.main()
