from __future__ import annotations
from copy import deepcopy
from .constants import DIT_SHA256,QWEN_SHA256,VAE_SHA256,SDCPP_COMMIT

def baseline_contract_snapshot()->dict:
    return {
      'inputs':{
        'dit':{'sha256':DIT_SHA256},
        'qwen':{'sha256':QWEN_SHA256},
        'vae':{'sha256':VAE_SHA256,'variation':'pytorch/vae-only'},
      },
      'runtime_commit':SDCPP_COMMIT,'backend':'cpu','host':'127.0.0.1','default_profile':'demo',
      'profiles':{'demo':{'width':512,'height':512},'balanced':{'width':640,'height':640},'research':{'width':1024,'height':1024}},
      'steps':4,'cfg':1.0,'threads':4,'real_acceptance_starts':1,
      'acceptance_artifact_sha256':'a'*64,'fetched_artifact_sha256':'a'*64,
      'evidence_files':['metadata/contract.json','metadata/local-acceptance.json','artifacts/release-acceptance-512.png'],
      'manifest_paths':['metadata/contract.json','metadata/local-acceptance.json','artifacts/release-acceptance-512.png'],
      'secret_scan_pass':True,'server_stop_pass':True,'allow_explicit_resolution':False,'explicit_resolution_accepted':False,
      'notebook_execution_count_null':True,'notebook_outputs_empty':True,'notebook_english':True,'notebook_vietnamese':True,
      'evidence_completed':True,'overall_pass':True,
      'public_state':'NOT_RUN','public_unauth_401':True,'public_tunnel_target':'http://127.0.0.1:8091','gateway_upstream':'http://127.0.0.1:8090','public_acceptance_generation_starts':0,
    }

def validate_contract_snapshot(d:dict)->list[str]:
    e=[]
    if d.get('inputs',{}).get('dit',{}).get('sha256')!=DIT_SHA256:e.append('Q8_HASH')
    if d.get('inputs',{}).get('qwen',{}).get('sha256')!=QWEN_SHA256:e.append('QWEN_HASH')
    vae=d.get('inputs',{}).get('vae',{})
    if vae.get('sha256')!=VAE_SHA256:e.append('VAE_HASH')
    if vae.get('variation')!='pytorch/vae-only':e.append('VAE_VARIATION')
    if d.get('runtime_commit')!=SDCPP_COMMIT:e.append('RUNTIME_COMMIT')
    if d.get('backend')!='cpu':e.append('BACKEND')
    if d.get('host')!='127.0.0.1':e.append('HOST')
    if d.get('default_profile')!='demo':e.append('DEFAULT_PROFILE')
    for name,size in [('demo',512),('balanced',640),('research',1024)]:
        p=d.get('profiles',{}).get(name,{})
        if p.get('width')!=size or p.get('height')!=size:e.append(f'PROFILE_{name.upper()}')
    if d.get('steps')!=4:e.append('STEPS')
    if float(d.get('cfg',-1))!=1.0:e.append('CFG')
    if d.get('threads')!=4:e.append('THREADS')
    if d.get('real_acceptance_starts')!=1:e.append('REAL_ACCEPTANCE_COUNT')
    if d.get('acceptance_artifact_sha256')!=d.get('fetched_artifact_sha256'):e.append('ARTIFACT_HASH')
    for f in d.get('evidence_files',[]):
        low=f.lower()
        if low.endswith(('.gguf','.safetensors','.ckpt','.bin')):e.append('MODEL_WEIGHT_IN_EVIDENCE')
        if 'token' in low or 'secret' in low:e.append('SECRET_NAMED_FILE')
    for p in d.get('manifest_paths',[]):
        if p.startswith('/') or '..' in p.split('/'):e.append('NONPORTABLE_MANIFEST')
    if not d.get('secret_scan_pass'):e.append('SECRET_SCAN')
    if not d.get('server_stop_pass'):e.append('SERVER_STOP')
    if not d.get('allow_explicit_resolution') and d.get('explicit_resolution_accepted'):e.append('EXPLICIT_RESOLUTION')
    if not d.get('notebook_execution_count_null'):e.append('NOTEBOOK_EXECUTION')
    if not d.get('notebook_outputs_empty'):e.append('NOTEBOOK_OUTPUT')
    if not d.get('notebook_english'):e.append('NOTEBOOK_EN')
    if not d.get('notebook_vietnamese'):e.append('NOTEBOOK_VI')
    if d.get('overall_pass') and not d.get('evidence_completed'):e.append('PASS_WITHOUT_EVIDENCE')
    if d.get('public_state')=='PASS':
        if not d.get('public_unauth_401'):e.append('PUBLIC_401')
        if d.get('public_tunnel_target')!='http://127.0.0.1:8091':e.append('PUBLIC_TARGET')
        if d.get('gateway_upstream')!='http://127.0.0.1:8090':e.append('PUBLIC_UPSTREAM')
        if d.get('public_acceptance_generation_starts')!=0:e.append('PUBLIC_GENERATION')
    return e
