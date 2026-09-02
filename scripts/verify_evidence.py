#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

from app.artifacts import inspect_png
from app.constants import (
    CANONICAL_PROMPT,
    CANONICAL_SEED,
    DIT_BYTES,
    DIT_FILENAME,
    DIT_SHA256,
    QWEN_FILENAME,
    QWEN_SHA256,
    SDCPP_COMMIT,
    SDCPP_SHORT,
    VAE_BYTES,
    VAE_FILENAME,
    VAE_SHA256,
)
from app.contracts import validate_contract_snapshot

class EvidenceError(RuntimeError): pass

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def _json(path:Path, label:str)->dict:
    if not path.is_file(): raise EvidenceError(f'{label} missing: {path.relative_to(path.parents[1]) if len(path.parents)>1 else path.name}')
    try: doc=json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc: raise EvidenceError(f'{label} invalid JSON: {exc}') from exc
    if not isinstance(doc,dict): raise EvidenceError(f'{label} must be a JSON object')
    return doc

def scan_hygiene(root:Path)->None:
    for p in root.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(root).as_posix(); low=rel.lower()
        if low.endswith(('.gguf','.safetensors','.ckpt','.pt','.pth')):raise EvidenceError(f'model weight forbidden: {rel}')
        if any(x in Path(rel).name.lower() for x in ('token','credential','secret')):raise EvidenceError(f'secret-named file forbidden: {rel}')
        if p.stat().st_size>4*1024*1024 and not low.endswith('.png'):continue
        try:text=p.read_text(errors='ignore')
        except Exception:continue
        if re.search(r'Authorization:\s*Bearer\s+[A-Za-z0-9._~+/-]{8,}',text,re.I):raise EvidenceError(f'Bearer secret in {rel}')
        if re.search(r'(?i)(api[_-]?token|bearer[_-]?token|secret)\s*[=:]\s*["\']?[A-Za-z0-9._~+/-]{16,}',text):raise EvidenceError(f'credential-like value in {rel}')

def verify_manifest(root:Path)->None:
    mf=root/'MANIFEST.sha256'; mj=root/'MANIFEST.json'
    if not mf.is_file():raise EvidenceError('MANIFEST.sha256 missing')
    if not mj.is_file():raise EvidenceError('MANIFEST.json missing')
    sha_entries={}
    for i,line in enumerate(mf.read_text().splitlines(),1):
        if not line.strip():continue
        try:
            digest,rel=line.split(None,1)
        except ValueError:raise EvidenceError(f'bad manifest line {i}')
        rel=rel.strip()
        if rel.startswith('*'):rel=rel[1:]
        if rel.startswith('/') or '..' in Path(rel).parts:raise EvidenceError(f'nonportable manifest path: {rel}')
        p=root/rel
        if not p.is_file():raise EvidenceError(f'manifest file missing: {rel}')
        if sha(p)!=digest:raise EvidenceError(f'manifest SHA mismatch: {rel}')
        sha_entries[rel]=digest
    try: doc=json.loads(mj.read_text())
    except Exception as exc: raise EvidenceError(f'MANIFEST.json invalid: {exc}') from exc
    entries=doc.get('files') if isinstance(doc,dict) else None
    if not isinstance(entries,list):raise EvidenceError('MANIFEST.json files must be a list')
    json_paths=set()
    for item in entries:
        if not isinstance(item,dict):raise EvidenceError('MANIFEST.json item invalid')
        rel=item.get('path')
        if not isinstance(rel,str) or rel.startswith('/') or '..' in Path(rel).parts:raise EvidenceError(f'nonportable MANIFEST.json path: {rel}')
        p=root/rel
        if not p.is_file():raise EvidenceError(f'MANIFEST.json file missing: {rel}')
        if p.stat().st_size!=item.get('bytes'):raise EvidenceError(f'MANIFEST.json byte mismatch: {rel}')
        if sha(p)!=item.get('sha256'):raise EvidenceError(f'MANIFEST.json SHA mismatch: {rel}')
        if rel in json_paths:raise EvidenceError(f'duplicate MANIFEST.json path: {rel}')
        json_paths.add(rel)
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.name not in ('MANIFEST.json','MANIFEST.sha256')}
    if json_paths!=actual:
        missing=sorted(actual-json_paths); extra=sorted(json_paths-actual)
        raise EvidenceError(f'MANIFEST.json completeness mismatch missing={missing} extra={extra}')
    expected_sha=actual|{'MANIFEST.json'}
    if set(sha_entries)!=expected_sha:raise EvidenceError('MANIFEST.sha256 completeness mismatch')

def _expect(condition:bool, code:str)->None:
    if not condition: raise EvidenceError(code)

def _verify_preflight(doc:dict)->None:
    _expect(doc.get('status')=='PASS','PREFLIGHT_STATUS')
    _expect(doc.get('runtime_commit_expected')==SDCPP_COMMIT,'PREFLIGHT_RUNTIME_EXPECTED')
    version=str(doc.get('runtime_version_output',''))
    _expect(SDCPP_COMMIT in version or SDCPP_SHORT in version,'PREFLIGHT_RUNTIME_ACTUAL')
    devices=str(doc.get('runtime_devices_output',''))
    low_devices=devices.lower()
    _expect('cpu' in low_devices,'PREFLIGHT_RUNTIME_CPU_MISSING')
    _expect(not any(x in low_devices for x in ('cuda','vulkan','metal','hip','sycl','opencl','musa')),'PREFLIGHT_RUNTIME_ACCELERATOR')
    _expect(doc.get('host')=='127.0.0.1','PREFLIGHT_HOST')
    _expect(doc.get('port')==8090,'PREFLIGHT_PORT')
    mem=doc.get('mem_available_kb'); min_mem=doc.get('min_mem_available_kb')
    disk=doc.get('disk_free_bytes'); min_disk=doc.get('min_disk_free_bytes')
    _expect(isinstance(mem,int) and isinstance(min_mem,int) and mem>=min_mem>0,'PREFLIGHT_MEMORY_ACTUAL')
    _expect(isinstance(disk,int) and isinstance(min_disk,int) and disk>=min_disk>0,'PREFLIGHT_DISK_ACTUAL')
    gates=doc.get('gates')
    _expect(isinstance(gates,dict) and bool(gates),'PREFLIGHT_GATES_MISSING')
    bad=[k for k,v in gates.items() if v!='PASS']
    _expect(not bad,'PREFLIGHT_GATE_FAIL:'+','.join(bad))
    inputs=doc.get('inputs')
    _expect(isinstance(inputs,dict),'PREFLIGHT_INPUTS')
    expected={
        'dit':(DIT_FILENAME,DIT_BYTES,DIT_SHA256,'gguf/q8-0'),
        'qwen':(QWEN_FILENAME,None,QWEN_SHA256,'gguf/q4-k-m'),
        'vae':(VAE_FILENAME,VAE_BYTES,VAE_SHA256,'pytorch/vae-only'),
    }
    for key,(filename,size,digest,variation) in expected.items():
        item=inputs.get(key) if isinstance(inputs,dict) else None
        _expect(isinstance(item,dict),f'PREFLIGHT_{key.upper()}_MISSING')
        _expect(item.get('filename')==filename,f'PREFLIGHT_{key.upper()}_FILENAME')
        if size is not None:_expect(item.get('bytes')==size,f'PREFLIGHT_{key.upper()}_BYTES')
        else:_expect(isinstance(item.get('bytes'),int) and item.get('bytes')>0,f'PREFLIGHT_{key.upper()}_BYTES')
        _expect(item.get('sha256')==digest,f'PREFLIGHT_{key.upper()}_SHA256')
        _expect(item.get('variation')==variation,f'PREFLIGHT_{key.upper()}_VARIATION')

def _verify_telemetry(doc:dict)->None:
    elapsed=doc.get('elapsed_ms')
    _expect(isinstance(elapsed,int) and elapsed>=0,'RUN_TELEMETRY_ELAPSED')
    peak=doc.get('peak_sd_cli_rss_kb')
    minimum=doc.get('minimum_mem_available_kb')
    _expect(isinstance(peak,int) and peak>0,'RUN_TELEMETRY_PEAK_RSS')
    _expect(isinstance(minimum,int) and minimum>0,'RUN_TELEMETRY_MIN_MEM')

def verify_semantics(root:Path, contract:dict)->dict:
    pre=_json(root/'metadata/preflight.sanitized.json','preflight')
    local=_json(root/'metadata/local-acceptance.json','local acceptance')
    counts=_json(root/'metadata/real-generation-count.json','real generation count')
    stop=_json(root/'metadata/server-stop.json','server stop')
    report=_json(root/'RELEASE-REPORT.json','release report')
    _verify_preflight(pre)

    _expect(local.get('status')=='PASS' and local.get('mode')=='REAL','LOCAL_ACCEPTANCE_STATUS')
    _expect(local.get('prompt')==CANONICAL_PROMPT,'LOCAL_ACCEPTANCE_PROMPT')
    _expect(local.get('seed')==CANONICAL_SEED,'LOCAL_ACCEPTANCE_SEED')
    _expect(local.get('profile')=='demo','LOCAL_ACCEPTANCE_PROFILE')
    _expect(local.get('public_tunnel_enabled') is False,'LOCAL_ACCEPTANCE_PUBLIC_STATE')
    request_id=local.get('request_id')
    _expect(isinstance(request_id,str) and request_id and Path(request_id).name==request_id,'LOCAL_ACCEPTANCE_REQUEST_ID')
    _expect(counts.get('canonical_real_acceptance_starts')==1,'REAL_ACCEPTANCE_COUNT_ACTUAL')
    _expect(stop.get('server_stop_pass') is True,'SERVER_STOP_ACTUAL')
    _expect(stop.get('no_orphan_sd_cli_pass') is True,'NO_ORPHAN_SD_CLI_ACTUAL')
    _expect(report.get('status')=='PASS','PHASE_REPORT_STATUS')
    _expect(report.get('CORE_LOCAL_DEMO')=='PASS','PHASE_REPORT_CORE_LOCAL')
    _expect(report.get('EVIDENCE_COLLECTION')=='PASS','PHASE_REPORT_EVIDENCE')

    png=root/'artifacts/release-acceptance-512.png'
    if not png.is_file(): raise EvidenceError('ACCEPTANCE_PNG_MISSING')
    try: actual_artifact=inspect_png(png,512,512)
    except Exception as exc: raise EvidenceError(f'ACCEPTANCE_PNG_INVALID:{exc}') from exc
    local_art=local.get('artifact')
    _expect(isinstance(local_art,dict),'LOCAL_ACCEPTANCE_ARTIFACT')
    for field in ('bytes','sha256','width','height','format'):
        _expect(local_art.get(field)==actual_artifact.get(field),f'LOCAL_ARTIFACT_{field.upper()}')

    run_dir=root/'runs'/request_id
    req=_json(run_dir/'request.json','run request')
    telemetry=_json(run_dir/'telemetry.json','run telemetry')
    result=_json(run_dir/'result.json','run result')
    for name in ('stdout.log','stderr.log'):
        _expect((run_dir/name).is_file(),f'RUN_{name.upper().replace(".","_")}_MISSING')
    _expect(req.get('prompt')==CANONICAL_PROMPT,'RUN_REQUEST_PROMPT')
    _expect(req.get('seed')==CANONICAL_SEED,'RUN_REQUEST_SEED')
    _expect(req.get('profile')=='demo','RUN_REQUEST_PROFILE')
    _expect(req.get('client_request_id')==request_id,'RUN_REQUEST_ID')
    _verify_telemetry(telemetry)
    _expect(result.get('request_id')==request_id,'RUN_RESULT_REQUEST_ID')
    _expect(result.get('status')=='succeeded','RUN_RESULT_STATUS')
    _expect(result.get('profile')=='demo','RUN_RESULT_PROFILE')
    result_art=result.get('artifact')
    _expect(isinstance(result_art,dict),'RUN_RESULT_ARTIFACT')
    for field in ('bytes','sha256','width','height','format'):
        _expect(result_art.get(field)==actual_artifact.get(field),f'RUN_RESULT_ARTIFACT_{field.upper()}')
    _expect(result.get('seed')==CANONICAL_SEED,'RUN_RESULT_SEED')
    _expect(result.get('exit_code')==0,'RUN_RESULT_EXIT_CODE')
    _expect(result.get('elapsed_ms')==telemetry.get('elapsed_ms'),'RUN_RESULT_ELAPSED')

    _expect(contract.get('real_acceptance_starts')==counts.get('canonical_real_acceptance_starts'),'CONTRACT_COUNT_CROSSCHECK')
    _expect(contract.get('acceptance_artifact_sha256')==actual_artifact['sha256'],'CONTRACT_ARTIFACT_SHA_CROSSCHECK')
    _expect(contract.get('fetched_artifact_sha256')==actual_artifact['sha256'],'CONTRACT_FETCHED_SHA_CROSSCHECK')
    _expect(contract.get('server_stop_pass') is True,'CONTRACT_STOP_CROSSCHECK')
    expected_run_files={f'runs/{request_id}/{name}' for name in ('request.json','stdout.log','stderr.log','telemetry.json','result.json')}
    evidence_files=set(contract.get('evidence_files',[]))
    _expect(expected_run_files.issubset(evidence_files),'CONTRACT_RUN_EVIDENCE_LIST')
    return {'request_id':request_id,'artifact_sha256':actual_artifact['sha256'],'actual_evidence':'PASS'}

def verify(root:Path)->dict:
    verify_manifest(root);scan_hygiene(root)
    contract_path=root/'metadata/contract.json'
    if not contract_path.is_file():raise EvidenceError('metadata/contract.json missing')
    contract=_json(contract_path,'contract')
    errors=validate_contract_snapshot(contract)
    if errors:raise EvidenceError('contract errors: '+','.join(errors))
    semantic=verify_semantics(root,contract)
    return {'status':'PASS','contract_errors':[],'manifest':'PASS','hygiene':'PASS','semantic':'PASS',**semantic}

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument('root');args=ap.parse_args()
    try:r=verify(Path(args.root))
    except EvidenceError as e:print(f'RELEASE_EVIDENCE_VERIFY=FAIL\nERROR={e}');return 2
    print(json.dumps(r,indent=2));print('RELEASE_EVIDENCE_VERIFY=PASS');return 0
if __name__=='__main__':raise SystemExit(main())
