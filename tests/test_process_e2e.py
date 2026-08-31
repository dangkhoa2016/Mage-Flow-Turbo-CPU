import json, os, signal, socket, subprocess, sys, tempfile, time, unittest
from pathlib import Path
from urllib.request import Request, urlopen

class ProcessE2ETests(unittest.TestCase):
    def test_fake_server_process_lifecycle_http_and_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); out=root/'outputs'; runs=root/'runs'; out.mkdir(); runs.mkdir()
            s=socket.socket(); s.bind(('127.0.0.1',0)); port=s.getsockname()[1]; s.close()
            cfg={
                'sd_cli':'/unused/sd-cli','dit_q8':'/unused/Mage-Flow-Turbo-DiT-Q8_0.gguf',
                'qwen':'/unused/Qwen3VL-4B-Instruct-Q4_K_M.gguf','vae':'/unused/diffusion_pytorch_model.safetensors',
                'output_dir':str(out),'runs_dir':str(runs),'host':'127.0.0.1','port':port,'timeout_seconds':2700,
            }
            cfgp=root/'service-config.json'; cfgp.write_text(json.dumps(cfg))
            env={**os.environ,'MAGE_ALLOW_ALT_PORT':'1'}
            stdout_file=(root/'server.stdout.log').open('w+'); stderr_file=(root/'server.stderr.log').open('w+')
            proc=subprocess.Popen([sys.executable,'-m','app.server','--config',str(cfgp),'--fake'],stdout=stdout_file,stderr=stderr_file,text=True,env=env)
            base=f'http://127.0.0.1:{port}'
            try:
                ready=False
                for _ in range(50):
                    if proc.poll() is not None: break
                    try:
                        ready=json.loads(urlopen(base+'/readyz',timeout=.2).read()).get('ready') is True
                        if ready: break
                    except Exception: pass
                    time.sleep(.05)
                if not ready:
                    proc.wait(timeout=1)
                    stdout_file.flush(); stderr_file.flush(); stdout_file.seek(0); stderr_file.seek(0)
                    self.fail(f'fake process not ready rc={proc.returncode} stdout={stdout_file.read()!r} stderr={stderr_file.read()!r}')
                body=json.dumps({'prompt':'Một con cáo đỏ nhỏ.','seed':42,'profile':'demo'},ensure_ascii=False).encode('utf-8')
                req=Request(base+'/v1/images/generate',data=body,headers={'Content-Type':'application/json'},method='POST')
                result=json.loads(urlopen(req,timeout=3).read())
                self.assertEqual(result['status'],'succeeded')
                self.assertEqual(result['profile'],'demo')
                self.assertEqual(result['seed'],42)
                png=urlopen(base+result['artifact_url'],timeout=2).read()
                self.assertTrue(png.startswith(b'\x89PNG\r\n\x1a\n'))
            finally:
                if proc.poll() is None:
                    proc.send_signal(signal.SIGTERM)
                    try: proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        proc.kill(); proc.wait(timeout=2)
            stdout_file.close(); stderr_file.close()
            self.assertEqual(proc.returncode,0)

if __name__=='__main__': unittest.main()
