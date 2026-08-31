#!/usr/bin/env bash
set -Eeuo pipefail
RUNTIME="${MAGE_RUNTIME_ROOT:-/kaggle/working/mage-flow-turbo-runtime}"
PIDFILE="$RUNTIME/state/server.pid"
if [[ ! -s "$PIDFILE" ]]; then echo 'RELEASE_SERVER_STATUS=STOPPED'; exit 1; fi
pid="$(cat "$PIDFILE")"
kill -0 "$pid" 2>/dev/null || { echo 'RELEASE_SERVER_STATUS=STALE_PID'; exit 2; }
python3 - <<'PY'
from urllib.request import urlopen
print(urlopen('http://127.0.0.1:8090/readyz',timeout=2).read().decode())
PY
echo "RELEASE_SERVER_STATUS=RUNNING pid=$pid"
