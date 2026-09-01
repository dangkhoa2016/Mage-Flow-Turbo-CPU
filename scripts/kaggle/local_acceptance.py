#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, sys, time
from pathlib import Path
from urllib.request import Request, urlopen

SOURCE_ROOT=Path(__file__).resolve().parents[2]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0,str(SOURCE_ROOT))

from app.constants import CANONICAL_PROMPT, CANONICAL_SEED
from app.artifacts import inspect_png

def get_json(url): return json.loads(urlopen(url, timeout=5).read().decode('utf-8'))
def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--base-url',default='http://127.0.0.1:8090')
    ap.add_argument('--runtime-root',default=os.environ.get('MAGE_RUNTIME_ROOT','/kaggle/working/mage-flow-turbo-runtime'))
    ap.add_argument('--fake',action='store_true',help='Marks acceptance as fake; does not count as canonical real acceptance.')
    args=ap.parse_args()
    rr=Path(args.runtime_root); state=rr/'state'; evidence=rr/'evidence'; state.mkdir(parents=True,exist_ok=True); evidence.mkdir(parents=True,exist_ok=True)
    health=get_json(args.base_url+'/healthz'); ready=get_json(args.base_url+'/readyz'); info=get_json(args.base_url+'/v1/info')
    if health.get('status')!='ok' or not ready.get('ready') or info.get('backend')!='cpu' or info.get('default_profile')!='demo':
        raise SystemExit('CORE_LOCAL_PREFLIGHT=FAIL')
    count_file=state/'real-generation-count.json'
    counts={'canonical_real_acceptance_starts':0}
    if count_file.exists(): counts=json.loads(count_file.read_text())
    if not args.fake:
        if counts.get('canonical_real_acceptance_starts',0) >= 1 and os.environ.get('MAGE_ALLOW_NEW_ACCEPTANCE','0')!='1':
            raise SystemExit('RELEASE_ONE_REAL_ACCEPTANCE_POLICY=FAIL already-started')
        counts['canonical_real_acceptance_starts']=counts.get('canonical_real_acceptance_starts',0)+1
        count_file.write_text(json.dumps(counts,indent=2)+'\n')
    payload={'prompt':CANONICAL_PROMPT,'seed':CANONICAL_SEED,'client_request_id':f"release-acceptance-{int(time.time())}",'profile':'demo'}
    raw=json.dumps(payload,ensure_ascii=False).encode('utf-8')
    req=Request(args.base_url+'/v1/images/generate',data=raw,headers={'Content-Type':'application/json'},method='POST')
    # Intentionally exactly one POST. Do not automatically retry after this point.
    started=time.monotonic(); response=json.loads(urlopen(req,timeout=int(os.environ.get('MAGE_HTTP_ACCEPTANCE_TIMEOUT_SECONDS','1600'))).read().decode('utf-8')); http_elapsed_ms=int((time.monotonic()-started)*1000)
    if response.get('status')!='succeeded': raise SystemExit('CORE_LOCAL_GENERATION=FAIL')
    art_url=args.base_url+response['artifact_url']; png=urlopen(art_url,timeout=30).read()
    out=evidence/'release-acceptance-512.png'; out.write_bytes(png)
    inspected=inspect_png(out,512,512)
    if inspected['sha256'] != response['artifact']['sha256']: raise SystemExit('RELEASE_ARTIFACT_HASH_AGREEMENT=FAIL')
    report={'schema_version':1,'mode':'FAKE' if args.fake else 'REAL','status':'PASS','profile':'demo','prompt':CANONICAL_PROMPT,'seed':CANONICAL_SEED,'http_elapsed_ms':http_elapsed_ms,'request_id':response['request_id'],'artifact':inspected,'artifact_url_path':response['artifact_url'],'public_tunnel_enabled':False}
    (state/'local-acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    print('CORE_LOCAL_DEMO=PASS' if not args.fake else 'CORE_LOCAL_DEMO_FAKE=PASS')
    print('RELEASE_ONE_REAL_ACCEPTANCE_POLICY=PASS' if not args.fake else 'RELEASE_ONE_REAL_ACCEPTANCE_POLICY=NOT_APPLICABLE_FAKE')
    return 0
if __name__=='__main__': raise SystemExit(main())
