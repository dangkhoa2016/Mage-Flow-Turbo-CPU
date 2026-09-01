import json,tempfile,threading,unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request,urlopen
from app.config import ServiceConfig
from app.service import build_server
from scripts.kaggle.auth_gateway import build_gateway, validate_upstream, GatewayConfigError, RateLimiter

class AuthGatewayTests(unittest.TestCase):
    def setUp(self):
        self.td=tempfile.TemporaryDirectory(); root=Path(self.td.name)
        cfg=ServiceConfig('/x','/d','/q','/v',str(root/'o'),str(root/'r'))
        self.backend=build_server(cfg,fake=True,listen_port=0); threading.Thread(target=self.backend.serve_forever,daemon=True).start()
        self.up=f"http://127.0.0.1:{self.backend.server_address[1]}"
        self.token='super-secret-test-token'
        self.gateway=build_gateway(token=self.token,upstream=self.up,listen_port=0,min_post_interval=0)
        threading.Thread(target=self.gateway.serve_forever,daemon=True).start()
        self.base=f"http://127.0.0.1:{self.gateway.server_address[1]}"
    def tearDown(self):
        self.gateway.shutdown(); self.gateway.server_close(); self.backend.shutdown(); self.backend.server_close(); self.td.cleanup()
    def test_unauthenticated_is_401(self):
        with self.assertRaises(HTTPError) as cm: urlopen(self.base+'/healthz',timeout=3)
        self.assertEqual(cm.exception.code,401)
    def test_authenticated_health_is_forwarded(self):
        req=Request(self.base+'/healthz',headers={'Authorization':'Bearer '+self.token})
        self.assertEqual(json.loads(urlopen(req,timeout=3).read())['status'],'ok')
    def test_non_loopback_upstream_rejected(self):
        with self.assertRaises(GatewayConfigError): validate_upstream('https://example.com')
    def test_rate_limiter_can_emit_rejection(self):
        r=RateLimiter(60)
        self.assertTrue(r.allow('client'))
        self.assertFalse(r.allow('client'))

if __name__=='__main__': unittest.main()
