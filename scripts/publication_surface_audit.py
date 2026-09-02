#!/usr/bin/env python3
from __future__ import annotations
import argparse, os, re, subprocess, sys
from pathlib import Path


def _s(*parts):
    return ''.join(parts)


FORBIDDEN_PATHS = {
    '00-START-HERE.md', 'BUILD-INFO.json', 'RELEASE-STATE.md',
    _s('docs/PHASE-', 'F', '-V2.1-DESIGN-SPEC.md'),
    _s('docs/PHASE-', 'G', '2-PUBLICATION-INTEGRATION.md'),
    _s('docs/OPENCODE-CODEX-PRE-PUSH-', 'CORR', 'ECTIVE', '-RUNBOOK.md'),
    _s('notebooks/kaggle-', 'phase-', 'g', '-public-dataset-acceptance.ipynb'),
    'scripts/collect_implementation_evidence.sh',
    _s('scripts/verify_', 'pre_', 'push', '_repo.py'),
    'scripts/kaggle/package-review-source.sh',
    _s('.github/workflows/', 'phase-', 'f', '.yml'),
    '.github/workflows/build-portable-runtime.yml',
}
REQUIRED_PATHS = {
    'README.md', 'README.vi.md', 'LICENSE', 'notebooks/kaggle-cpu-production-demo.ipynb',
    '.github/workflows/ci.yml', '.github/workflows/portable-runtime.yml',
    '.github/CONTRIBUTING.md', '.github/CODE_OF_CONDUCT.md', '.github/SECURITY.md', '.github/SUPPORT.md',
    '.github/CODEOWNERS', '.github/PULL_REQUEST_TEMPLATE.md', '.github/dependabot.yml',
    '.github/ISSUE_TEMPLATE/bug_report.yml', '.github/ISSUE_TEMPLATE/feature_request.yml', '.github/ISSUE_TEMPLATE/config.yml',
}
FORBIDDEN_PATTERNS = [
    r'Phase\s+F', r'Phase\s+G',
    _s('PHASE', '_', 'F'), _s('PHASE', '_', 'G'),
    _s('phase', '-', 'f'), _s('phase', '-', 'g'),
    _s('phase', '_', 'f'), _s('phase', '_', 'g'),
    _s('MageFlow', 'Phase', 'F'), _s('mage-flow-turbo-', 'phase-', 'f'),
    _s('portable CPU runtime ', 'candidate'),
    _s(r'\b', 'corr', 'ective', r'\b'),
    _s(r'\b', 'PRE', '_', 'PUSH', r'\b'),
]
TEXT_SUFFIXES={'.md','.py','.sh','.json','.yml','.yaml','.txt','.ipynb'}
BADGE_TOKEN='actions/workflows/ci.yml/badge.svg'
BILINGUAL_PAIRS=[
    ('README.md','README.vi.md'),('CHANGELOG.md','CHANGELOG.vi.md'),
    ('docs/RELEASE-NOTES-v1.0.0.md','docs/RELEASE-NOTES-v1.0.0.vi.md'),
    ('docs/TESTING.md','docs/TESTING.vi.md'),('docs/TROUBLESHOOTING.md','docs/TROUBLESHOOTING.vi.md'),
    ('docs/kaggle-production-demo-notebook.md','docs/kaggle-production-demo-notebook.vi.md')
]

def git_files(root: Path):
    cp=subprocess.run(['git','-C',str(root),'ls-files','-z'],check=True,stdout=subprocess.PIPE)
    return [Path(x.decode()) for x in cp.stdout.split(b'\0') if x]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.')
    root=Path(ap.parse_args().root).resolve(); errors=[]
    tracked=set(p.as_posix() for p in git_files(root))
    for p in sorted(FORBIDDEN_PATHS & tracked): errors.append(f'forbidden tracked path: {p}')
    for p in sorted(REQUIRED_PATHS - tracked): errors.append(f'required path missing: {p}')
    rx=[re.compile(x,re.I if 'PHASE_' not in x else 0) for x in FORBIDDEN_PATTERNS]
    for rel in sorted(tracked):
        p=root/rel
        if p.suffix.lower() not in TEXT_SUFFIXES or not p.is_file(): continue
        try: text=p.read_text(encoding='utf-8')
        except UnicodeDecodeError: continue
        for r in rx:
            m=r.search(text)
            if m: errors.append(f'forbidden terminology {r.pattern!r} in {rel}'); break
    for en,vi in BILINGUAL_PAIRS:
        for rel in (en,vi):
            p=root/rel
            if not p.is_file(): errors.append(f'bilingual document missing: {rel}'); continue
            text=p.read_text(encoding='utf-8')
            if BADGE_TOKEN not in text: errors.append(f'CI badge missing: {rel}')
            if 'Language / Ngôn ngữ' not in text: errors.append(f'language switch missing: {rel}')
    if errors:
        print('PUBLICATION_SURFACE_AUDIT=FAIL')
        for e in errors: print('ERROR='+e)
        return 2
    print('PUBLICATION_SURFACE_AUDIT=PASS')
    print(f'TRACKED_FILES={len(tracked)}')
    return 0
if __name__=='__main__': raise SystemExit(main())
