#!/usr/bin/env bash
set -Eeuo pipefail
RUNTIME="${MAGE_RUNTIME_ROOT:-/kaggle/working/mage-flow-turbo-runtime}"
mkdir -p "$RUNTIME/logs"
{
  date -u +%FT%TZ
  uname -a
  python3 --version
  cmake --version | head -1 || true
  c++ --version | head -1 || true
  lscpu || true
  free -b || true
  df -h /kaggle/working 2>/dev/null || df -h .
  command -v nvidia-smi || true
  nvidia-smi || true
} > "$RUNTIME/logs/environment.log" 2>&1
# Hardware may expose a GPU executable/device, but the inference policy remains CPU-only.
echo 'RELEASE_CPU_ONLY_POLICY=PASS' | tee -a "$RUNTIME/logs/environment.log"
