#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,shutil,socket,subprocess,sys
from pathlib import Path

SOURCE_ROOT=Path(__file__).resolve().parents[2]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0,str(SOURCE_ROOT))

from app.constants import SDCPP_COMMIT,SDCPP_SHORT
from app.inputs import resolve_canonical_inputs

WEIGHT_SUFFIXES={'.gguf','.safetensors','.ckpt','.pt','.pth','.onnx'}

def mem_available_kb():
    try:
        for line in Path('/proc/meminfo').read_text().splitlines():
            if line.startswith('MemAvailable:'): return int(line.split()[1])
    except OSError: pass
    return None

def port_available(host:str='127.0.0.1',port:int=8090)->bool:
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    try:
        s.bind((host,port)); return True
    except OSError:
        return False
    finally:
        s.close()

def source_weight_files(root:Path)->list[Path]:
    found=[]
    for p in root.rglob('*'):
        if not p.is_file(): continue
        if p.suffix.lower() in WEIGHT_SUFFIXES: found.append(p)
    return sorted(found)

def prove_writable(root:Path)->bool:
    root.mkdir(parents=True,exist_ok=True)
    probe=root/'.release-write-probe'
    try:
        probe.write_text('ok\n',encoding='utf-8')
        return probe.read_text(encoding='utf-8')=='ok\n'
    except OSError:
        return False
    finally:
        try: probe.unlink()
        except FileNotFoundError: pass

def git_source_state(root:Path)->tuple[str,bool]:
    try:
        head=subprocess.run(['git','-C',str(root),'rev-parse','HEAD'],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,check=True).stdout.strip()
        dirty=subprocess.run(['git','-C',str(root),'status','--porcelain'],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,check=True).stdout.strip()
        return head,not bool(dirty)
    except (OSError,subprocess.SubprocessError):
        return '',False

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--input-root',default=os.environ.get('MAGE_INPUT_ROOT','/kaggle/input'))
    ap.add_argument('--runtime-root',default=os.environ.get('MAGE_RUNTIME_ROOT','/kaggle/working/mage-flow-turbo-runtime'))
    ap.add_argument('--source-root',default=os.environ.get('MAGE_SOURCE_ROOT'))
    ap.add_argument('--sd-cli',default=os.environ.get('MAGE_SD_CLI'))
    ap.add_argument('--min-mem-kb',type=int,default=int(os.environ.get('MAGE_MIN_MEM_AVAILABLE_KB',str(16*1024*1024))))
    ap.add_argument('--host',default=os.environ.get('MAGE_HOST','127.0.0.1'))
    ap.add_argument('--port',type=int,default=int(os.environ.get('MAGE_PORT','8090')))
    ap.add_argument('--output',default=None)
    args=ap.parse_args()
    rr=Path(args.runtime_root); state=rr/'state'; outputs=rr/'outputs'; runs=rr/'runs'; logs=rr/'logs'
    source_root=Path(args.source_root).resolve() if args.source_root else SOURCE_ROOT
    for p in (state,outputs,runs,logs): p.mkdir(parents=True,exist_ok=True)
    sd=Path(args.sd_cli) if args.sd_cli else rr/'bin/sd-cli'
    gates={}; errors=[]

    source_git_head,source_git_clean=git_source_state(source_root)
    if not source_git_head:
        gates['RELEASE_SOURCE_GIT_PROVENANCE']='FAIL'; errors.append('source Git HEAD unavailable')
    elif not source_git_clean:
        gates['RELEASE_SOURCE_GIT_PROVENANCE']='FAIL'; errors.append('source Git worktree is not clean')
    else:
        gates['RELEASE_SOURCE_GIT_PROVENANCE']='PASS'

    if args.host!='127.0.0.1': errors.append('MAGE_HOST must be 127.0.0.1')
    if os.environ.get('MAGE_BACKEND','cpu').lower()!='cpu': errors.append('MAGE_BACKEND must be cpu')
    gates['RELEASE_CPU_ONLY_POLICY']='PASS' if not any(e.startswith('MAGE_') for e in errors) else 'FAIL'

    try:
        inputs=resolve_canonical_inputs(Path(args.input_root)); gates['RELEASE_MODEL_IDENTITIES']='PASS'
    except Exception as exc:
        inputs=None; gates['RELEASE_MODEL_IDENTITIES']='FAIL'; errors.append(str(exc))

    version=''; devices=''
    if not sd.is_file() or not os.access(sd,os.X_OK):
        gates['RELEASE_SD_CLI_PRESENT']='FAIL'; errors.append(f'sd-cli missing: {sd}')
    else:
        gates['RELEASE_SD_CLI_PRESENT']='PASS'
        try:
            cp=subprocess.run([str(sd),'--version'],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30,check=False)
            version=cp.stdout.strip()
            if cp.returncode!=0 or (SDCPP_SHORT not in version and SDCPP_COMMIT not in version):
                gates['RELEASE_RUNTIME_COMMIT']='FAIL'; errors.append(f'runtime commit mismatch: {version!r}')
            else: gates['RELEASE_RUNTIME_COMMIT']='PASS'
            devcp=subprocess.run([str(sd),'--list-devices'],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30,check=False)
            devices=devcp.stdout.strip()
            accel=('cuda','vulkan','metal','hip','sycl','opencl','musa')
            if devcp.returncode!=0 or 'CPU' not in devices or any(x in devices.lower() for x in accel):
                gates['RELEASE_RUNTIME_CPU_ONLY']='FAIL'; errors.append(f'non-CPU device list: {devices!r}')
            else: gates['RELEASE_RUNTIME_CPU_ONLY']='PASS'
        except (OSError,subprocess.SubprocessError) as exc:
            gates['RELEASE_RUNTIME_COMMIT']='FAIL'; gates['RELEASE_RUNTIME_CPU_ONLY']='FAIL'; errors.append(f'runtime probe failed: {exc}')

    avail=mem_available_kb()
    if avail is not None and avail < args.min_mem_kb:
        gates['RELEASE_MEMORY_GATE']='FAIL'; errors.append(f'MemAvailable {avail} kB < {args.min_mem_kb} kB')
    else: gates['RELEASE_MEMORY_GATE']='PASS'

    usage=shutil.disk_usage(rr)
    min_disk=int(os.environ.get('MAGE_MIN_DISK_FREE_BYTES',str(2*1024**3)))
    if usage.free<min_disk:
        gates['RELEASE_DISK_GATE']='FAIL'; errors.append(f'disk free {usage.free} < {min_disk}')
    else: gates['RELEASE_DISK_GATE']='PASS'

    if not prove_writable(outputs) or not prove_writable(runs) or not prove_writable(logs) or not prove_writable(state):
        gates['RELEASE_RUNTIME_DIRS_WRITABLE']='FAIL'; errors.append('one or more runtime directories are not writable')
    else: gates['RELEASE_RUNTIME_DIRS_WRITABLE']='PASS'

    if not port_available(args.host,args.port):
        gates['RELEASE_LOCAL_PORT_AVAILABLE']='FAIL'; errors.append(f'{args.host}:{args.port} is already in use')
    else: gates['RELEASE_LOCAL_PORT_AVAILABLE']='PASS'

    weights=source_weight_files(source_root)
    if weights:
        gates['RELEASE_SOURCE_NO_MODEL_WEIGHTS']='FAIL'; errors.append('model weights found in source: '+','.join(p.relative_to(source_root).as_posix() for p in weights[:10]))
    else: gates['RELEASE_SOURCE_NO_MODEL_WEIGHTS']='PASS'

    status='PASS' if all(v=='PASS' for v in gates.values()) else 'FAIL'
    doc={'schema_version':3,'status':status,'source_git_head':source_git_head,'source_git_clean':source_git_clean,'runtime_commit_expected':SDCPP_COMMIT,'runtime_version_output':version,'runtime_devices_output':devices,'sd_cli':str(sd.resolve()) if sd.exists() else str(sd),'source_root':str(source_root),'host':args.host,'port':args.port,'mem_available_kb':avail,'min_mem_available_kb':args.min_mem_kb,'disk_free_bytes':usage.free,'min_disk_free_bytes':min_disk,'gates':gates,'errors':errors}
    if inputs:
        doc['inputs']={k:{'path':str(v.path),'bytes':v.bytes,'sha256':v.sha256} for k,v in inputs.items()}
        service={'sd_cli':str(sd.resolve()),'dit_q8':str(inputs['dit'].path),'qwen':str(inputs['qwen'].path),'vae':str(inputs['vae'].path),'output_dir':str(outputs),'runs_dir':str(runs),'host':args.host,'port':args.port,'timeout_seconds':int(os.environ.get('MAGE_REQUEST_TIMEOUT_CEILING_SECONDS','2700'))}
        (state/'service-config.json').write_text(json.dumps(service,indent=2)+'\n')
    out=Path(args.output) if args.output else state/'preflight.json'; out.write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n')
    print(json.dumps(doc,indent=2,sort_keys=True)); print(f'RELEASE_PREFLIGHT={status}')
    return 0 if status=='PASS' else 3
if __name__=='__main__': raise SystemExit(main())
