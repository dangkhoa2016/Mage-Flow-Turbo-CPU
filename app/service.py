from __future__ import annotations
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import threading
from urllib.parse import urlparse, unquote
from .backend import generate as backend_generate
from .config import ServiceConfig, validate_generation_payload
from .constants import DIT_FILENAME,DIT_BYTES,DIT_SHA256,QWEN_FILENAME,QWEN_SHA256,VAE_FILENAME,VAE_BYTES,VAE_SHA256,SDCPP_COMMIT
from .profiles import load_profile, primary_profiles
from .resources import resource_status

MAX_JSON_BYTES = 16 * 1024

class BusyError(RuntimeError): pass
class ResourceAdmissionError(RuntimeError): pass

class ServiceState:
    def __init__(self, config: ServiceConfig, *, generator=backend_generate, fake: bool=False):
        self.config=config; self.generator=generator; self.fake=fake
        self.lock=threading.Lock(); self.shutting_down=False
        Path(config.output_dir).mkdir(parents=True,exist_ok=True); Path(config.runs_dir).mkdir(parents=True,exist_ok=True)
    @property
    def busy(self): return self.lock.locked()
    def generate(self,payload: object):
        data=validate_generation_payload(payload)
        if not self.lock.acquire(blocking=False): raise BusyError('BUSY_SINGLE_FLIGHT')
        try:
            p=load_profile(data['profile'])
            if not self.fake:
                rs=resource_status(p.name, self.config.runs_dir)
                if not rs['memory_ok'] or not rs['disk_ok']:
                    raise ResourceAdmissionError('RESOURCE_ADMISSION_FAILED')
            return self.generator(config=self.config,prompt=data['prompt'],seed=data['seed'],profile=p,client_request_id=data['client_request_id'],fake=self.fake)
        finally: self.lock.release()

class _Server(ThreadingHTTPServer):
    daemon_threads=True
    allow_reuse_address=True
    def __init__(self, address, handler, state):
        self.state=state
        super().__init__(address, handler)

class Handler(BaseHTTPRequestHandler):
    server_version='MageFlowTurboCPU/1.0'
    def log_message(self, fmt, *args):
        return
    @property
    def state(self): return self.server.state
    def _send_json(self,status,obj):
        raw=json.dumps(obj,ensure_ascii=False,separators=(',',':')).encode('utf-8')
        self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def _error(self,status,code,message): self._send_json(status,{'status':'error','error':code,'message':message})
    def do_GET(self):
        path=urlparse(self.path).path
        if path=='/healthz': return self._send_json(200,{'status':'ok','service':'mage-flow-turbo-cpu'})
        if path=='/readyz':
            if self.state.fake:
                rs={'profile':'demo','memory_ok':True,'disk_ok':True,'fake_backend':True}
            else:
                rs=resource_status('demo',self.state.config.runs_dir)
            ready=(not self.state.shutting_down) and rs['memory_ok'] and rs['disk_ok']
            return self._send_json(200 if ready else 503,{'ready':ready,'backend':'cpu','busy':self.state.busy,'generation_concurrency':1,'resource_gate':rs})
        if path=='/v1/info':
            profiles={k:{'width':v.width,'height':v.height,'steps':v.steps,'cfg_scale':v.cfg_scale,'threads':v.threads,'timeout_seconds':v.timeout_seconds} for k,v in primary_profiles().items()}
            return self._send_json(200,{
                'service':'mage-flow-turbo-cpu','backend':'cpu','runtime_commit':SDCPP_COMMIT,'default_profile':'demo','profiles':profiles,
                'inputs':{'dit':{'filename':DIT_FILENAME,'bytes':DIT_BYTES,'sha256':DIT_SHA256},'qwen':{'filename':QWEN_FILENAME,'sha256':QWEN_SHA256},'vae':{'filename':VAE_FILENAME,'bytes':VAE_BYTES,'sha256':VAE_SHA256,'variation':'pytorch/vae-only'}},
                'single_flight':True,'public_backend_direct_exposure':False})
        prefix='/v1/artifacts/'
        if path.startswith(prefix):
            name=unquote(path[len(prefix):])
            if not name or Path(name).name != name or not name.endswith('.png'):
                return self._error(400,'INVALID_ARTIFACT_NAME','safe PNG basename required')
            p=(Path(self.state.config.output_dir)/name).resolve(); root=Path(self.state.config.output_dir).resolve()
            if p.parent != root or not p.is_file(): return self._error(404,'ARTIFACT_NOT_FOUND','artifact not found')
            raw=p.read_bytes(); self.send_response(200); self.send_header('Content-Type','image/png'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw); return
        self._error(404,'NOT_FOUND','unknown endpoint')
    def do_POST(self):
        path=urlparse(self.path).path
        if path!='/v1/images/generate': return self._error(404,'NOT_FOUND','unknown endpoint')
        try: n=int(self.headers.get('Content-Length','0'))
        except ValueError: return self._error(400,'BAD_LENGTH','invalid Content-Length')
        if n<=0 or n>MAX_JSON_BYTES: return self._error(413 if n>MAX_JSON_BYTES else 400,'BODY_SIZE','invalid request body size')
        try:
            payload=json.loads(self.rfile.read(n).decode('utf-8'))
            result=self.state.generate(payload)
        except UnicodeDecodeError: return self._error(400,'INVALID_UTF8','body must be UTF-8')
        except json.JSONDecodeError: return self._error(400,'INVALID_JSON','body must be JSON')
        except ValueError as exc: return self._error(400,'INVALID_REQUEST',str(exc))
        except BusyError as exc: return self._error(409,'BUSY_SINGLE_FLIGHT',str(exc))
        except ResourceAdmissionError as exc: return self._error(503,'RESOURCE_ADMISSION_FAILED',str(exc))
        except TimeoutError as exc: return self._error(504,'REQUEST_TIMEOUT',str(exc))
        except Exception as exc: return self._error(500,'INFERENCE_FAILED',str(exc))
        self._send_json(200,{'status':'succeeded','request_id':result.request_id,'profile':result.profile,'width':result.artifact['width'],'height':result.artifact['height'],'seed':result.seed,'backend':'cpu','elapsed_ms':result.elapsed_ms,'artifact':result.artifact,'artifact_url':f"/v1/artifacts/{result.artifact['filename']}"})

def build_server(config: ServiceConfig, *, fake: bool=False, listen_port: int | None=None, generator=backend_generate) -> ThreadingHTTPServer:
    if config.host!='127.0.0.1': raise ValueError('backend may bind only to 127.0.0.1')
    state=ServiceState(config,generator=generator,fake=fake)
    return _Server((config.host, config.port if listen_port is None else listen_port),Handler,state)
