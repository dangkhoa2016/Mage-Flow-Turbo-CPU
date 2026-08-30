from __future__ import annotations
from pathlib import Path

def read_proc_rss_kb(pid: int) -> int | None:
    try:
        text = Path(f"/proc/{pid}/status").read_text(errors="replace")
    except OSError:
        return None
    for line in text.splitlines():
        if line.startswith("VmRSS:"):
            try: return int(line.split()[1])
            except (IndexError, ValueError): return None
    return None

def read_mem_available_kb() -> int | None:
    try: text = Path("/proc/meminfo").read_text(errors="replace")
    except OSError: return None
    for line in text.splitlines():
        if line.startswith("MemAvailable:"):
            try: return int(line.split()[1])
            except (IndexError, ValueError): return None
    return None
