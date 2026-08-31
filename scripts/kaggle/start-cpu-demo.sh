#!/usr/bin/env bash
set -Eeuo pipefail
SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUNTIME="${MAGE_RUNTIME_ROOT:-/kaggle/working/mage-flow-turbo-runtime}"
STATE="$RUNTIME/state"; LOGS="$RUNTIME/logs"; PIDFILE="$STATE/server.pid"
mkdir -p "$STATE" "$LOGS"
if [[ -s "$PIDFILE" ]]; then
  old="$(cat "$PIDFILE")"
  if kill -0 "$old" 2>/dev/null; then echo "RELEASE_SERVER_ALREADY_RUNNING=FAIL pid=$old"; exit 31; fi
  rm -f "$PIDFILE"
fi
export PYTHONPATH="$SOURCE_ROOT${PYTHONPATH:+:$PYTHONPATH}"
# Standalone start is safe by default: rerun preflight. Notebook may explicitly reuse
# the immediately preceding PASS to avoid hashing multi-GB immutable Kaggle inputs twice.
if [[ "${MAGE_REUSE_PREFLIGHT:-0}" == "1" ]]; then
  python3 - "$STATE/preflight.json" "$STATE/service-config.json" <<'PY'
import json,sys
from pathlib import Path
pre,cfg=map(Path,sys.argv[1:])
if not pre.is_file() or not cfg.is_file(): raise SystemExit('RELEASE_PREFLIGHT_REUSE=FAIL missing state')
d=json.loads(pre.read_text())
if d.get('status')!='PASS': raise SystemExit('RELEASE_PREFLIGHT_REUSE=FAIL prior preflight not PASS')
if d.get('host')!='127.0.0.1' or int(d.get('port',0))!=8090: raise SystemExit('RELEASE_PREFLIGHT_REUSE=FAIL topology drift')
print('RELEASE_PREFLIGHT_REUSE=PASS')
PY
else
  python3 "$SOURCE_ROOT/scripts/kaggle/preflight.py"
fi
CFG="$STATE/service-config.json"
nohup python3 -m app.server --config "$CFG" >"$LOGS/server.stdout.log" 2>"$LOGS/server.stderr.log" &
pid=$!; echo "$pid" > "$PIDFILE"
for _ in $(seq 1 60); do
  if ! kill -0 "$pid" 2>/dev/null; then echo 'RELEASE_SERVER_START=FAIL'; tail -100 "$LOGS/server.stderr.log" || true; exit 33; fi
  if python3 - <<'PY'
from urllib.request import urlopen
import json
try:
 d=json.loads(urlopen('http://127.0.0.1:8090/readyz',timeout=1).read()); raise SystemExit(0 if d.get('ready') else 1)
except Exception: raise SystemExit(1)
PY
  then echo "RELEASE_SERVER_START=PASS pid=$pid"; exit 0; fi
  sleep 1
done
echo 'RELEASE_SERVER_READY=FAIL'; exit 34
