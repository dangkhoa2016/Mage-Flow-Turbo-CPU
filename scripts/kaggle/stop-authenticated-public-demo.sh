#!/usr/bin/env bash
set -Eeuo pipefail
RUNTIME="${MAGE_RUNTIME_ROOT:-/kaggle/working/mage-flow-turbo-runtime}"; PUB="$RUNTIME/public"
for pair in cloudflared gateway; do
  f="$PUB/$pair.pid"; [[ -s "$f" ]] || continue; pid="$(cat "$f")"; kill -TERM "$pid" 2>/dev/null || true
  for _ in $(seq 1 10); do kill -0 "$pid" 2>/dev/null || break; sleep .2; done
  kill -KILL "$pid" 2>/dev/null || true; rm -f "$f"
done
rm -f "$PUB/public-url"
echo 'RELEASE_PUBLIC_DEMO_STOP=PASS'
