#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,os
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request,urlopen

def request(url,token=None):
    headers={}
    if token: headers['Authorization']='Bearer '+token
    return urlopen(Request(url,headers=headers),timeout=30)

def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def main()->int:
    rr=Path(os.environ.get('MAGE_RUNTIME_ROOT','/kaggle/working/mage-flow-turbo-runtime')); pub=rr/'public'; state=rr/'state'
    token_file=pub/'bearer-token'; url_file=pub/'public-url'; local_file=state/'local-acceptance.json'
    if not token_file.is_file() or not url_file.is_file() or not local_file.is_file():
        print('AUTHENTICATED_PUBLIC_DEMO=FAIL_MISSING_PREREQUISITE'); return 2
    token=token_file.read_text().strip(); base=url_file.read_text().strip().rstrip('/'); local=json.loads(local_file.read_text())
    try:
        request(base+'/healthz')
        print('AUTHENTICATED_PUBLIC_DEMO=FAIL_UNAUTHENTICATED_NOT_REJECTED'); return 3
    except HTTPError as e:
        if e.code!=401: print(f'AUTHENTICATED_PUBLIC_DEMO=FAIL_UNAUTH_STATUS_{e.code}'); return 4
    health=json.loads(request(base+'/healthz',token).read()); ready=json.loads(request(base+'/readyz',token).read()); info=json.loads(request(base+'/v1/info',token).read())
    if health.get('status')!='ok' or not ready.get('ready') or info.get('backend')!='cpu':
        print('AUTHENTICATED_PUBLIC_DEMO=FAIL_GATEWAY_METADATA'); return 5
    # This script deliberately performs only GETs. It never POSTs generation.
    art=request(base+local['artifact_url_path'],token).read(); remote_sha=sha_bytes(art); expected=local['artifact']['sha256']
    if remote_sha!=expected:
        print('AUTHENTICATED_PUBLIC_DEMO=FAIL_ARTIFACT_HASH'); return 6
    report={'schema_version':1,'status':'PASS','unauthenticated_health_status':401,'authenticated_health_status':200,'authenticated_ready_status':200,'authenticated_info_status':200,'artifact_fetch_status':200,'artifact_sha256':remote_sha,'local_artifact_sha256':expected,'public_acceptance_generation_starts':0,'tunnel_target':'http://127.0.0.1:8091','gateway_upstream':'http://127.0.0.1:8090'}
    (state/'public-acceptance.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2)); print('AUTHENTICATED_PUBLIC_DEMO=PASS'); return 0
if __name__=='__main__': raise SystemExit(main())
