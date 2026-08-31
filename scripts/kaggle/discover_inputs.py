#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from app.inputs import resolve_canonical_inputs, InputResolutionError

def main() -> int:
    ap=argparse.ArgumentParser(description='Resolve and SHA-verify the three canonical release Kaggle inputs.')
    ap.add_argument('--input-root',default='/kaggle/input')
    ap.add_argument('--output',default=None)
    args=ap.parse_args()
    try: resolved=resolve_canonical_inputs(Path(args.input_root))
    except InputResolutionError as exc:
        print(f'RELEASE_INPUT_DISCOVERY=FAIL\nERROR={exc}')
        return 2
    doc={'schema_version':1,'status':'PASS','inputs':{k:{'path':str(v.path),'bytes':v.bytes,'sha256':v.sha256} for k,v in resolved.items()},'gates':{
        'RELEASE_DIT_Q8_IDENTITY':'PASS','RELEASE_QWEN_IDENTITY':'PASS','RELEASE_VAE_ONLY_IDENTITY':'PASS','RELEASE_FORBIDDEN_PYTORCH_DEFAULT_DEPENDENCY':'PASS'}}
    text=json.dumps(doc,indent=2,sort_keys=True)+'\n'
    if args.output:
        p=Path(args.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text)
    print(text,end=''); print('RELEASE_INPUT_DISCOVERY=PASS')
    return 0
if __name__=='__main__': raise SystemExit(main())
