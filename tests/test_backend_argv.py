import unittest
from pathlib import Path
from app.config import ServiceConfig
from app.backend import build_sd_cli_argv
from app.profiles import load_profile

class BackendArgvTests(unittest.TestCase):
    def test_canonical_argv_and_prompt_is_single_item(self):
        c = ServiceConfig(sd_cli='/x/sd-cli', dit_q8='/m/dit.gguf', qwen='/m/qwen.gguf', vae='/m/vae.safetensors', output_dir='/tmp/o', runs_dir='/tmp/r')
        prompt = 'Một con cáo đỏ nhỏ trong rừng xanh; $(touch /tmp/NOPE)'
        argv = build_sd_cli_argv(c, prompt=prompt, seed=42, profile=load_profile('demo'), output_path='/tmp/a.png')
        self.assertEqual(argv[0], '/x/sd-cli')
        self.assertIn('--backend', argv); self.assertIn('cpu', argv)
        self.assertIn('--params-backend', argv)
        self.assertIn('--diffusion-model', argv); self.assertIn('/m/dit.gguf', argv)
        self.assertIn('--llm', argv); self.assertIn('/m/qwen.gguf', argv)
        self.assertIn('--vae', argv); self.assertIn('/m/vae.safetensors', argv)
        self.assertIn('--diffusion-fa', argv)
        self.assertIn('--output', argv)
        self.assertIn(prompt, argv)
        self.assertEqual(argv[argv.index('-W')+1], '512')
        self.assertEqual(argv[argv.index('-H')+1], '512')
        self.assertEqual(argv[argv.index('--steps')+1], '4')
        self.assertEqual(argv[argv.index('--cfg-scale')+1], '1.0')
        self.assertEqual(argv[argv.index('-t')+1], '4')

if __name__ == '__main__': unittest.main()
