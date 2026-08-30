from __future__ import annotations
import shutil
from pathlib import Path
from .telemetry import read_mem_available_kb

GIB=1024**3
KIB_PER_GIB=1024**2

def required_resources(profile_name:str)->tuple[int,int]:
    if profile_name=='research': return (20*KIB_PER_GIB,3*GIB)
    return (16*KIB_PER_GIB,2*GIB)

def resource_status(profile_name:str, workspace: str|Path)->dict:
    min_mem_kb,min_disk_bytes=required_resources(profile_name)
    mem=read_mem_available_kb(); disk=shutil.disk_usage(Path(workspace)).free
    return {'profile':profile_name,'mem_available_kb':mem,'disk_free_bytes':disk,'min_mem_available_kb':min_mem_kb,'min_disk_free_bytes':min_disk_bytes,'memory_ok':mem is None or mem>=min_mem_kb,'disk_ok':disk>=min_disk_bytes}
