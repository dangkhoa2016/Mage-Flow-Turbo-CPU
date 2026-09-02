#!/usr/bin/env bash
set -Eeuo pipefail
SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUNTIME="${MAGE_RUNTIME_ROOT:-/kaggle/working/mage-flow-turbo-runtime}"; mkdir -p "$RUNTIME/state"
# Clean shutdown is part of the evidence gate. Both stop helpers are idempotent.
if [[ -s "$RUNTIME/public/gateway.pid" || -s "$RUNTIME/public/cloudflared.pid" ]]; then bash "$SOURCE_ROOT/scripts/kaggle/stop-authenticated-public-demo.sh"; fi
if bash "$SOURCE_ROOT/scripts/kaggle/stop-cpu-demo.sh"; then
  printf '{"server_stop_pass":true,"no_orphan_sd_cli_pass":true}\n' > "$RUNTIME/state/server-stop.json"
else
  printf '{"server_stop_pass":false,"no_orphan_sd_cli_pass":false}\n' > "$RUNTIME/state/server-stop.json"
  echo 'EVIDENCE_COLLECTION=FAIL_SERVER_STOP'; exit 61
fi
export PYTHONPATH="$SOURCE_ROOT${PYTHONPATH:+:$PYTHONPATH}"
python3 "$SOURCE_ROOT/scripts/kaggle/collect_evidence.py"
