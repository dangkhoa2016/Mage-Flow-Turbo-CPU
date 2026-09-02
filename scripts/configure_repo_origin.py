#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re,subprocess
from pathlib import Path
MARKER='__MAGE_REPO_URL__'
def normalize(url:str)->str:
    u=url.strip()
    if u.startswith('git@github.com:'): u='https://github.com/'+u.split(':',1)[1]
    elif u.startswith('ssh://git@github.com/'): u='https://github.com/'+u.split('ssh://git@github.com/',1)[1]
    if u.startswith('http://github.com/'): u='https://github.com/'+u.split('http://github.com/',1)[1]
    if not u.startswith('https://github.com/'): raise ValueError(f'GitHub origin required, got {url!r}')
    return u.removesuffix('.git').rstrip('/')
def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--apply',action='store_true'); ap.add_argument('--repo-url',default=None); args=ap.parse_args()
    raw=args.repo_url or subprocess.check_output(['git','remote','get-url','origin'],text=True).strip(); url=normalize(raw)
    nb=Path('notebooks/kaggle-cpu-production-demo.ipynb'); text=nb.read_text(encoding='utf-8')
    if MARKER not in text and url in text: print(f'REPO_ORIGIN_ALREADY_FINALIZED={url}'); return 0
    if MARKER not in text: raise SystemExit('REPO_ORIGIN_FINALIZE=FAIL marker missing and requested URL not present')
    print(f'REPO_ORIGIN_RESOLVED={url}')
    if not args.apply: print('REPO_ORIGIN_APPLY=NOT_RUN'); return 0
    nb.write_text(text.replace(MARKER,url),encoding='utf-8')
    bi=Path('BUILD-INFO.json')
    data=json.loads(bi.read_text()) if bi.exists() else {}; data['repository_origin']=url; bi.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    print('REPO_ORIGIN_FINALIZE=PASS'); return 0
if __name__=='__main__': raise SystemExit(main())
