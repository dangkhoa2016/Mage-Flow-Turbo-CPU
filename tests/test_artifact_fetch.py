import json,tempfile,threading,unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request,urlopen
from app.config import ServiceConfig
from app.service import build_server
class ArtifactFetchTests(unittest.TestCase):
    def test_safe_basename_only(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td); c=ServiceConfig('/x','/d','/q','/v',str(r/'o'),str(r/'runs'))
            s=build_server(c,fake=True,listen_port=0); t=threading.Thread(target=s.serve_forever,daemon=True);t.start();base=f'http://127.0.0.1:{s.server_address[1]}'
            try:
                body=json.dumps({'prompt':'x','seed':1}).encode();res=json.loads(urlopen(Request(base+'/v1/images/generate',data=body,headers={'Content-Type':'application/json'},method='POST'),timeout=4).read())
                self.assertEqual(urlopen(base+res['artifact_url'],timeout=3).status,200)
                with self.assertRaises(HTTPError) as cm:urlopen(base+'/v1/artifacts/../secret',timeout=3)
                self.assertIn(cm.exception.code,(400,404))
            finally:s.shutdown();s.server_close();t.join(2)
if __name__=='__main__':unittest.main()
