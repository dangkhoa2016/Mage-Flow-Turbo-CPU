#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${MAGE_RUNTIME_ROOT:-/kaggle/working/mage-flow-turbo-runtime}"
SRC="$ROOT/sdcpp-src"
BUILD="$ROOT/sdcpp-build"
BINDIR="$ROOT/bin"
BIN="$BINDIR/sd-cli"
BOOTSTRAP_LOG="$ROOT/logs/bootstrap.log"
COMMIT="6b3edaaf32cc19e5bb2d819c788bd557eddc8eba"
REPO="https://github.com/leejet/stable-diffusion.cpp.git"
MODE="${MAGE_RUNTIME_MODE:-auto}"
PREBUILT="${MAGE_PREBUILT_SD_CLI:-}"
PREBUILT_SHA256="${MAGE_PREBUILT_SD_CLI_SHA256:-}"
JOBS="${MAGE_BUILD_JOBS:-4}"
TAIL_LINES="${MAGE_BOOTSTRAP_ERROR_TAIL_LINES:-60}"

mkdir -p "$ROOT"/{state,logs,runs,outputs,public,evidence} "$BINDIR"
: > "$BOOTSTRAP_LOG"

say() { printf '%s\n' "$*"; }
run_logged() {
  if ! "$@" >>"$BOOTSTRAP_LOG" 2>&1; then
    say "Runtime preparation command failed: $*"
    say "--- bootstrap.log (last ${TAIL_LINES} lines) ---"
    tail -n "$TAIL_LINES" "$BOOTSTRAP_LOG" || true
    return 1
  fi
}

verify_binary() {
  [[ -x "$BIN" ]] || return 1
  local v d
  v="$($BIN --version 2>&1 || true)"
  d="$($BIN --list-devices 2>&1 || true)"
  [[ "$v" == *6b3edaa* ]] || return 1
  [[ "$d" == *CPU* ]] || return 1
  if echo "$d" | grep -Eiq 'CUDA|Vulkan|Metal|HIP|SYCL|OpenCL|MUSA'; then
    return 1
  fi
  printf '%s\n' "$v" > "$ROOT/state/sd-cli.version.txt"
  printf '%s\n' "$d" > "$ROOT/state/sd-cli.devices.txt"
  return 0
}

install_prebuilt() {
  [[ -n "$PREBUILT" && -f "$PREBUILT" ]] || return 1
  [[ -n "$PREBUILT_SHA256" ]] || return 1
  local check_file
  check_file="$(mktemp)"
  printf '%s  %s\n' "$PREBUILT_SHA256" "$PREBUILT" > "$check_file"
  if ! sha256sum -c "$check_file" >>"$BOOTSTRAP_LOG" 2>&1; then
    rm -f "$check_file"
    return 1
  fi
  rm -f "$check_file"
  cp "$PREBUILT" "$BIN"
  chmod +x "$BIN"
  verify_binary
}

build_source() {
  rm -rf "$SRC" "$BUILD" "$BINDIR"
  mkdir -p "$BINDIR"
  say '[1/4] Fetching pinned stable-diffusion.cpp source...'
  run_logged git clone --recursive "$REPO" "$SRC"
  run_logged git -C "$SRC" checkout --detach "$COMMIT"
  run_logged git -C "$SRC" submodule sync --recursive
  run_logged git -C "$SRC" submodule update --init --recursive
  local actual
  actual="$(git -C "$SRC" rev-parse HEAD)"
  [[ "$actual" == "$COMMIT" ]] || {
    say "RELEASE_RUNTIME_COMMIT=FAIL actual=$actual"
    return 21
  }
  say '[2/4] Configuring CPU-only runtime...'
  run_logged cmake -S "$SRC" -B "$BUILD" \
    -DCMAKE_BUILD_TYPE=Release \
    -DSD_CUDA=OFF -DSD_HIPBLAS=OFF -DSD_METAL=OFF -DSD_VULKAN=OFF \
    -DSD_OPENCL=OFF -DSD_SYCL=OFF -DSD_MUSA=OFF -DSD_RPC=OFF \
    -DGGML_NATIVE=ON
  say '[3/4] Building sd-cli only...'
  run_logged cmake --build "$BUILD" --config Release --target sd-cli -j "$JOBS"
  local cand=""
  for c in "$BUILD/bin/sd-cli" "$BUILD/sdcpp/bin/sd-cli" "$BUILD/sd-cli"; do
    [[ -x "$c" ]] && cand="$c" && break
  done
  [[ -n "$cand" ]] || {
    say 'RELEASE_SD_CLI_BUILD=FAIL'
    return 22
  }
  cp "$cand" "$BIN"
  chmod +x "$BIN"
  verify_binary || {
    say 'RELEASE_RUNTIME_IDENTITY=FAIL'
    return 23
  }
  say 'RELEASE_RUNTIME_SOURCE_BUILD=PASS'
}

case "$MODE" in
  auto|prebuilt|source) ;;
  *)
    say "RELEASE_RUNTIME_MODE=FAIL unsupported=$MODE"
    exit 24
    ;;
esac

printf 'RELEASE_BOOTSTRAP_STARTED=%s\n' "$(date -u +%FT%TZ)" >>"$BOOTSTRAP_LOG"
say "Preparing CPU runtime (mode=$MODE)..."

if verify_binary; then
  say 'RELEASE_SD_CLI_REUSE=PASS'
  say 'RELEASE_RUNTIME_REUSE=PASS'
elif [[ "$MODE" == "source" ]]; then
  build_source
elif install_prebuilt; then
  say 'RELEASE_PREBUILT_RUNTIME=PASS'
else
  if [[ "$MODE" == "prebuilt" ]]; then
    say 'RELEASE_PREBUILT_RUNTIME=FAIL'
    say 'Set MAGE_PREBUILT_SD_CLI and MAGE_PREBUILT_SD_CLI_SHA256 to a verified CPU-only sd-cli artifact.'
    exit 25
  fi
  say 'RELEASE_PREBUILT_FALLBACK=SOURCE'
  build_source
fi

say '[4/4] Verifying pinned CPU-only runtime...'
printf '%s\n' "$COMMIT" > "$ROOT/state/sdcpp-head.txt"
sha256sum "$BIN" > "$ROOT/state/sd-cli.sha256"
"$BIN" --help > "$ROOT/logs/sd-cli.help.txt" 2>&1 || true
"$BIN" --list-devices > "$ROOT/logs/sd-cli.devices.txt" 2>&1 || true

say 'Runtime ready.'
say 'RELEASE_SD_CLI_BUILD=PASS'
say 'RELEASE_RUNTIME_COMMIT=PASS'
say 'RELEASE_RUNTIME_CPU_ONLY=PASS'
say "BOOTSTRAP_LOG=$BOOTSTRAP_LOG"
