#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,os,shutil,subprocess,tempfile,zipfile
from pathlib import Path

FORBIDDEN_SUFFIXES={'.gguf','.safetensors','.ckpt','.pt','.pth','.onnx'}
EXCLUDE_SUFFIXES={'.zip','.gz','.pyc'}
EXCLUDE_PARTS={'__pycache__','.git','.venv','logs','outputs','state','evidence','cache'}

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def normalized_filesystem_files(root:Path)->list[Path]:
    files=[]
    for p in root.rglob('*'):
        if not p.is_file(): continue
        rel=p.relative_to(root)
        if any(x in EXCLUDE_PARTS for x in rel.parts): continue
        if p.suffix.lower() in EXCLUDE_SUFFIXES or p.name.endswith('.tar.gz') or p.name.endswith('.sha256'): continue
        if p.name in ('SOURCE-MANIFEST.json','SOURCE-MANIFEST.sha256'): continue
        files.append(rel)
    return sorted(files,key=lambda p:p.as_posix())

def git_files(root:Path)->list[Path]:
    cp=subprocess.run(['git','-C',str(root),'ls-files','-z'],check=True,stdout=subprocess.PIPE)
    return sorted((Path(x.decode()) for x in cp.stdout.split(b'\0') if x),key=lambda p:p.as_posix())

def verify_payload_file(root:Path,rel:Path)->None:
    if rel.is_absolute() or '..' in rel.parts: raise RuntimeError(f'unsafe source path: {rel}')
    if rel.suffix.lower() in FORBIDDEN_SUFFIXES: raise RuntimeError(f'model weight forbidden in source: {rel}')
    if any(x in EXCLUDE_PARTS for x in rel.parts): raise RuntimeError(f'runtime/generated path forbidden in source: {rel}')

def build(root:Path,out:Path,*,allow_placeholder:bool=False,filesystem:bool=False)->dict:
    root=root.resolve(); out=out.resolve()
    notebook=root/'notebooks/kaggle-cpu-production-demo.ipynb'
    if not allow_placeholder and '__MAGE_REPO_URL__' in notebook.read_text(encoding='utf-8'):
        raise RuntimeError('repository origin placeholder remains')
    rels=normalized_filesystem_files(root) if filesystem else git_files(root)
    with tempfile.TemporaryDirectory(prefix='mage-flow-source-stage.') as td:
        stage=Path(td)
        for rel in rels:
            verify_payload_file(root,rel)
            src=root/rel
            if not src.is_file(): raise RuntimeError(f'tracked source file missing: {rel}')
            dst=stage/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
        manifest=[]
        for p in sorted(stage.rglob('*')):
            if p.is_file(): manifest.append({'path':p.relative_to(stage).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
        (stage/'SOURCE-MANIFEST.json').write_text(json.dumps({'schema_version':1,'files':manifest},indent=2,sort_keys=True)+'\n',encoding='utf-8')
        lines=[]
        for p in sorted(stage.rglob('*')):
            if p.is_file() and p.name!='SOURCE-MANIFEST.sha256': lines.append(f"{sha(p)}  {p.relative_to(stage).as_posix()}")
        (stage/'SOURCE-MANIFEST.sha256').write_text('\n'.join(lines)+'\n',encoding='utf-8')
        out.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for p in sorted(stage.rglob('*')):
                if p.is_file(): z.write(p,p.relative_to(stage).as_posix())
        with tempfile.TemporaryDirectory(prefix='mage-flow-source-verify.') as vd:
            with zipfile.ZipFile(out) as z:
                for info in z.infolist():
                    q=Path(info.filename)
                    if q.is_absolute() or '..' in q.parts: raise RuntimeError(f'unsafe ZIP member: {info.filename}')
                z.extractall(vd)
            vr=Path(vd)
            subprocess.run(['sha256sum','-c','SOURCE-MANIFEST.sha256'],cwd=vr,check=True,stdout=subprocess.DEVNULL)
            # Structural hygiene recheck.
            for p in vr.rglob('*'):
                if p.is_file() and p.suffix.lower() in FORBIDDEN_SUFFIXES: raise RuntimeError(f'model weight in extracted source: {p.name}')
    digest=sha(out); side=Path(str(out)+'.sha256'); side.write_text(f'{digest}  {out.name}\n',encoding='utf-8')
    return {'archive':str(out),'sha256':digest,'sidecar':str(side),'file_count':len(rels),'cleanroom_verify':'PASS'}

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ap.add_argument('--output',required=True); ap.add_argument('--allow-placeholder',action='store_true'); ap.add_argument('--filesystem',action='store_true')
    a=ap.parse_args(); print(json.dumps(build(Path(a.root),Path(a.output),allow_placeholder=a.allow_placeholder,filesystem=a.filesystem),indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
