#!/usr/bin/env bash
set -Eeuo pipefail
SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUNTIME="${MAGE_RUNTIME_ROOT:-/kaggle/working/mage-flow-turbo-runtime}"; PUB="$RUNTIME/public"; mkdir -p "$PUB"
TOKEN_FILE="$PUB/bearer-token"; PIDFILE="$PUB/gateway.pid"; LOG="$PUB/gateway.log"
if [[ ! -s "$TOKEN_FILE" ]]; then python3 - <<PY
import secrets,os
p='$TOKEN_FILE'; open(p,'w').write(secrets.token_urlsafe(36)+'\n'); os.chmod(p,0o600)
PY
fi
[[ "$(stat -c %a "$TOKEN_FILE")" == 600 ]] || chmod 600 "$TOKEN_FILE"
if [[ -s "$PIDFILE" ]]; then
  old="$(cat "$PIDFILE")"
  if kill -0 "$old" 2>/dev/null; then echo 'RELEASE_AUTH_GATEWAY=ALREADY_RUNNING'; exit 0; fi
  rm -f "$PIDFILE"
fi
# Never steal an unrelated local listener.
python3 - <<'PY' || { echo 'RELEASE_GATEWAY_PORT_8091_AVAILABLE=FAIL'; exit 50; }
import socket
s=socket.socket()
try: s.bind(('127.0.0.1',8091))
except OSError: raise SystemExit(1)
finally: s.close()
PY
export PYTHONPATH="$SOURCE_ROOT${PYTHONPATH:+:$PYTHONPATH}"
nohup python3 "$SOURCE_ROOT/scripts/kaggle/auth_gateway.py" --token-file "$TOKEN_FILE" --upstream http://127.0.0.1:8090 --port 8091 >"$LOG" 2>&1 & gateway_pid=$!; echo "$gateway_pid" > "$PIDFILE"
ready=0
for _ in $(seq 1 30); do
  kill -0 "$gateway_pid" 2>/dev/null || break
  if python3 - <<PY
from urllib.request import Request,urlopen
from pathlib import Path
t=Path('$TOKEN_FILE').read_text().strip(); r=Request('http://127.0.0.1:8091/healthz',headers={'Authorization':'Bearer '+t})
try: raise SystemExit(0 if urlopen(r,timeout=1).status==200 else 1)
except Exception: raise SystemExit(1)
PY
  then ready=1; break; fi
  sleep 1
done
if [[ "$ready" != 1 ]]; then
  tail -100 "$LOG" || true
  kill -TERM "$gateway_pid" 2>/dev/null || true; rm -f "$PIDFILE"
  echo 'RELEASE_AUTH_GATEWAY=FAIL'; exit 51
fi
echo 'RELEASE_AUTH_GATEWAY=PASS'
if [[ "${ENABLE_PUBLIC_TUNNEL:-False}" == "True" || "${ENABLE_PUBLIC_TUNNEL:-0}" == "1" ]]; then
  CF="${CLOUDFLARED_BIN:-$(command -v cloudflared || true)}"
  [[ -n "$CF" && -x "$CF" ]] || { echo 'RELEASE_QUICK_TUNNEL=NOT_STARTED_CLOUDFLARED_MISSING'; exit 52; }
  "$CF" --version > "$PUB/cloudflared.version.txt" 2>&1 || true
  nohup "$CF" tunnel --no-autoupdate --url http://127.0.0.1:8091 >"$PUB/cloudflared.log" 2>&1 & cf_pid=$!; echo "$cf_pid" > "$PUB/cloudflared.pid"
  for _ in $(seq 1 60); do
    kill -0 "$cf_pid" 2>/dev/null || break
    url="$(grep -Eo 'https://[-a-z0-9]+\.trycloudflare\.com' "$PUB/cloudflared.log" | head -1 || true)"
    if [[ -n "$url" ]]; then printf '%s\n' "$url" > "$PUB/public-url"; echo "RELEASE_QUICK_TUNNEL=PASS url=$url"; exit 0; fi
    sleep 1
  done
  echo 'RELEASE_QUICK_TUNNEL=FAIL'; exit 53
else
  echo 'AUTHENTICATED_PUBLIC_DEMO=NOT_RUN'
fi
