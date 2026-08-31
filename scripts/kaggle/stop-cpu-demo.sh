#!/usr/bin/env bash
set -Eeuo pipefail
RUNTIME="${MAGE_RUNTIME_ROOT:-/kaggle/working/mage-flow-turbo-runtime}"
PIDFILE="$RUNTIME/state/server.pid"
no_orphan(){
  if pgrep -f "sd-cli.*Mage-Flow-Turbo-DiT-Q8_0.gguf" >/dev/null 2>&1; then echo 'RELEASE_NO_ORPHAN_SD_CLI=FAIL'; return 1; fi
  echo 'RELEASE_NO_ORPHAN_SD_CLI=PASS'; return 0
}
if [[ ! -s "$PIDFILE" ]]; then echo 'RELEASE_SERVER_STOP=NOT_RUNNING'; no_orphan; exit $?; fi
pid="$(cat "$PIDFILE")"
if ! kill -0 "$pid" 2>/dev/null; then rm -f "$PIDFILE"; echo 'RELEASE_SERVER_STOP=STALE_PID_CLEANED'; no_orphan; exit $?; fi
# Never terminate the coordinator while a generation is active; that could orphan sd-cli.
if python3 - <<'PYBUSY'
from urllib.request import urlopen
import json
try:
 d=json.loads(urlopen('http://127.0.0.1:8090/readyz',timeout=2).read()); raise SystemExit(1 if d.get('busy') else 0)
except Exception: raise SystemExit(0)
PYBUSY
then :; else echo 'RELEASE_SERVER_STOP=FAIL_BUSY'; exit 43; fi
cmd="$(tr '\0' ' ' </proc/$pid/cmdline 2>/dev/null || true)"
[[ "$cmd" == *"app.server"* ]] || { echo "RELEASE_SERVER_STOP=FAIL_UNOWNED_PID pid=$pid"; exit 41; }
kill -TERM "$pid"
for _ in $(seq 1 20); do kill -0 "$pid" 2>/dev/null || break; sleep .5; done
if kill -0 "$pid" 2>/dev/null; then kill -KILL "$pid"; fi
wait "$pid" 2>/dev/null || true
rm -f "$PIDFILE"
echo 'RELEASE_SERVER_STOP=PASS'
no_orphan
