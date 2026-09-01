#!/usr/bin/env python3
from __future__ import annotations
import argparse,hmac,http.client,json,time,threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse

class GatewayConfigError(ValueError): pass

def validate_upstream(value:str)->tuple[str,int]:
    u=urlparse(value)
    if u.scheme!='http' or u.hostname not in ('127.0.0.1','localhost') or not u.port:
        raise GatewayConfigError('gateway upstream must be an explicit loopback http://127.0.0.1:<port> URL')
    return ('127.0.0.1',u.port)

class RateLimiter:
    def __init__(self,min_interval:float): self.min_interval=max(0.0,float(min_interval)); self.last={}; self.lock=threading.Lock()
    def allow(self,key:str)->bool:
        now=time.monotonic()
        with self.lock:
            prev=self.last.get(key)
            if prev is not None and now-prev<self.min_interval: return False
            self.last[key]=now; return True

class _Gateway(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self,addr,handler,*,token,upstream,min_post_interval):
        self.token=token; self.up_host,self.up_port=validate_upstream(upstream); self.limiter=RateLimiter(min_post_interval)
        super().__init__(addr,handler)

class GatewayHandler(BaseHTTPRequestHandler):
    server_version='MageFlowAuthGateway/2.1'
    max_body=16*1024
    allowed_get_prefixes=('/healthz','/readyz','/v1/info','/v1/artifacts/')
    def log_message(self,fmt,*args): return
    def _json(self,status,obj):
        raw=json.dumps(obj,separators=(',',':')).encode(); self.send_response(status); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def _authorized(self):
        header=self.headers.get('Authorization','')
        prefix='Bearer '
        return header.startswith(prefix) and hmac.compare_digest(header[len(prefix):],self.server.token)
    def _admit(self):
        if not self._authorized(): self._json(401,{'error':'UNAUTHORIZED'}); return False
        return True
    def _proxy(self,method,body=None):
        conn=http.client.HTTPConnection(self.server.up_host,self.server.up_port,timeout=30 if method=='GET' else 2850)
        headers={}
        if body is not None: headers['Content-Type']='application/json'
        conn.request(method,self.path,body=body,headers=headers)
        res=conn.getresponse(); data=res.read()
        self.send_response(res.status)
        ctype=res.getheader('Content-Type') or 'application/octet-stream'; self.send_header('Content-Type',ctype); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data); conn.close()
    def do_GET(self):
        if not self._admit(): return
        path=urlparse(self.path).path
        if not any(path==p or (p.endswith('/') and path.startswith(p)) for p in self.allowed_get_prefixes): return self._json(404,{'error':'NOT_ALLOWED'})
        self._proxy('GET')
    def do_POST(self):
        if not self._admit(): return
        if urlparse(self.path).path!='/v1/images/generate': return self._json(404,{'error':'NOT_ALLOWED'})
        key=self.client_address[0]
        if not self.server.limiter.allow(key): return self._json(429,{'error':'RATE_LIMITED'})
        try: n=int(self.headers.get('Content-Length','0'))
        except ValueError: return self._json(400,{'error':'BAD_LENGTH'})
        if n<=0 or n>self.max_body: return self._json(413 if n>self.max_body else 400,{'error':'BODY_SIZE'})
        self._proxy('POST',self.rfile.read(n))

def build_gateway(*,token:str,upstream='http://127.0.0.1:8090',listen_host='127.0.0.1',listen_port=8091,min_post_interval=30.0):
    if listen_host!='127.0.0.1': raise GatewayConfigError('gateway must bind 127.0.0.1')
    if not isinstance(token,str) or len(token)<16: raise GatewayConfigError('Bearer token must be at least 16 characters')
    return _Gateway((listen_host,listen_port),GatewayHandler,token=token,upstream=upstream,min_post_interval=min_post_interval)

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--token-file',required=True); ap.add_argument('--upstream',default='http://127.0.0.1:8090'); ap.add_argument('--port',type=int,default=8091); ap.add_argument('--min-post-interval',type=float,default=30.0); args=ap.parse_args()
    from pathlib import Path
    token=Path(args.token_file).read_text().strip()
    server=build_gateway(token=token,upstream=args.upstream,listen_port=args.port,min_post_interval=args.min_post_interval)
    try: server.serve_forever(.25)
    except KeyboardInterrupt: pass
    finally: server.server_close()
    return 0
if __name__=='__main__': raise SystemExit(main())
