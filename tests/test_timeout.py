import tempfile,unittest,os
from pathlib import Path
from app.backend import generate
from app.config import ServiceConfig
from app.profiles import load_profile

class TimeoutTests(unittest.TestCase):
    def test_backend_timeout_terminates_fake_process_command(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); exe=root/'slow-sd-cli'
            exe.write_text('#!/usr/bin/env bash\nsleep 5\n',encoding='utf-8'); exe.chmod(0o755)
            c=ServiceConfig(str(exe),'/d','/q','/v',str(root/'out'),str(root/'runs'),timeout_seconds=0)
            with self.assertRaises(TimeoutError):
                generate(c,prompt='x',seed=1,profile=load_profile('demo'),client_request_id='timeout-test',fake=False)

if __name__=='__main__':unittest.main()
