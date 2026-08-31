import json, os, tempfile, threading, unittest
from pathlib import Path
from urllib.request import urlopen, Request
from app.config import ServiceConfig
from app.service import build_server

class FakeServerTests(unittest.TestCase):
    def setUp(self):
        self.td=tempfile.TemporaryDirectory(); root=Path(self.td.name)
        self.config=ServiceConfig('/x/sd-cli','/m/dit.gguf','/m/qwen.gguf','/m/vae.safetensors',str(root/'outputs'),str(root/'runs'),port=8090)
        self.server=build_server(self.config, fake=True, listen_port=0)
        self.thread=threading.Thread(target=self.server.serve_forever, daemon=True); self.thread.start()
        self.base=f'http://127.0.0.1:{self.server.server_address[1]}'
    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(2); self.td.cleanup()
    def _json(self,path): return json.loads(urlopen(self.base+path, timeout=3).read())
    def test_health_ready_info(self):
        self.assertEqual(self._json('/healthz')['status'],'ok')
        self.assertTrue(self._json('/readyz')['ready'])
        self.assertEqual(self._json('/v1/info')['default_profile'],'demo')
    def test_generate_and_fetch_artifact(self):
        body=json.dumps({'prompt':'Một con cáo đỏ nhỏ.','seed':42,'profile':'demo'}).encode()
        req=Request(self.base+'/v1/images/generate',data=body,headers={'Content-Type':'application/json'},method='POST')
        res=json.loads(urlopen(req,timeout=5).read())
        self.assertEqual(res['status'],'succeeded')
        data=urlopen(self.base+res['artifact_url'],timeout=3).read()
        self.assertTrue(data.startswith(b'\x89PNG'))
        self.assertEqual(res['artifact']['width'],512)
        self.assertEqual(res['profile'],'demo')
        self.assertEqual(res['seed'],42)

    def test_response_uses_validated_profile_metadata(self):
        body=json.dumps({'prompt':'Một con cáo đỏ nhỏ.','seed':7,'profile':'balanced'}).encode()
        req=Request(self.base+'/v1/images/generate',data=body,headers={'Content-Type':'application/json'},method='POST')
        res=json.loads(urlopen(req,timeout=5).read())
        self.assertEqual(res['profile'],'balanced')
        self.assertEqual(res['seed'],7)
        self.assertEqual((res['width'],res['height']),(640,640))

    def test_response_default_profile_remains_demo_even_if_environment_drifts(self):
        old=os.environ.get('MAGE_DEFAULT_PROFILE')
        os.environ['MAGE_DEFAULT_PROFILE']='balanced'
        try:
            body=json.dumps({'prompt':'Một con cáo đỏ nhỏ.','seed':9}).encode()
            req=Request(self.base+'/v1/images/generate',data=body,headers={'Content-Type':'application/json'},method='POST')
            res=json.loads(urlopen(req,timeout=5).read())
            self.assertEqual(res['profile'],'demo')
            self.assertEqual((res['width'],res['height']),(512,512))
        finally:
            if old is None: os.environ.pop('MAGE_DEFAULT_PROFILE',None)
            else: os.environ['MAGE_DEFAULT_PROFILE']=old

if __name__=='__main__': unittest.main()
