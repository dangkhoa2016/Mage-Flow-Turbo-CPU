#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"
[[ -z "$(git status --porcelain --untracked-files=all)" ]] || { echo 'RELEASE_SOURCE_WORKTREE_CLEAN=FAIL'; exit 71; }
! grep -q '__MAGE_REPO_URL__' notebooks/kaggle-cpu-production-demo.ipynb || { echo 'RELEASE_REPO_ORIGIN_FINALIZED=FAIL'; exit 72; }
python3 -m unittest discover -s tests -v
TS="$(date -u +%Y%m%dT%H%M%SZ)"; OUT="${1:-$PWD/mage-flow-turbo-cpu-kaggle-cpu-production-demo-source-$TS.zip}"
python3 scripts/build_source_package.py --root "$ROOT" --output "$OUT"
echo "RELEASE_SOURCE_ARCHIVE_REEXTRACT_VERIFY=PASS archive=$OUT"
