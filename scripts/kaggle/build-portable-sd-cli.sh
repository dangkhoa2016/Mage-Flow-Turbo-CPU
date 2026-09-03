#!/usr/bin/env bash
set -Eeuo pipefail

COMMIT="6b3edaaf32cc19e5bb2d819c788bd557eddc8eba"
REPO="https://github.com/leejet/stable-diffusion.cpp.git"
ROOT="${MAGE_PORTABLE_BUILD_ROOT:-$PWD/.portable-sd-cli-build}"
SRC="$ROOT/src"
BUILD="$ROOT/build"
OUT="$ROOT/out"
JOBS="${MAGE_BUILD_JOBS:-4}"
ARCHIVE_NAME="stable-diffusion-cpp-6b3edaa-portable-cpu-runtime.tar.gz"

rm -rf "$ROOT"
mkdir -p "$OUT"

git clone --recursive "$REPO" "$SRC"
git -C "$SRC" checkout --detach "$COMMIT"
git -C "$SRC" submodule sync --recursive
git -C "$SRC" submodule update --init --recursive
ACTUAL="$(git -C "$SRC" rev-parse HEAD)"
[[ "$ACTUAL" == "$COMMIT" ]]

cmake -S "$SRC" -B "$BUILD" \
  -DCMAKE_BUILD_TYPE=Release \
  -DSD_CUDA=OFF -DSD_HIPBLAS=OFF -DSD_METAL=OFF -DSD_VULKAN=OFF \
  -DSD_OPENCL=OFF -DSD_SYCL=OFF -DSD_MUSA=OFF -DSD_RPC=OFF \
  -DGGML_NATIVE=OFF
cmake --build "$BUILD" --config Release --target sd-cli -j "$JOBS"

CAND=""
for c in "$BUILD/bin/sd-cli" "$BUILD/sdcpp/bin/sd-cli" "$BUILD/sd-cli"; do
  [[ -x "$c" ]] && CAND="$c" && break
done
[[ -n "$CAND" ]]

cp "$CAND" "$OUT/sd-cli"
chmod +x "$OUT/sd-cli"
VERSION="$($OUT/sd-cli --version 2>&1 || true)"
DEVICES="$($OUT/sd-cli --list-devices 2>&1 || true)"
[[ "$VERSION" == *6b3edaa* ]]
[[ "$DEVICES" == *CPU* ]]
if echo "$DEVICES" | grep -Eiq 'CUDA|Vulkan|Metal|HIP|SYCL|OpenCL|MUSA'; then
  echo 'portable runtime unexpectedly exposes a non-CPU backend' >&2
  exit 31
fi

(
  cd "$OUT"
  sha256sum sd-cli > SHA256SUMS
)
SHA="$(awk '{print $1}' "$OUT/SHA256SUMS")"
cat > "$OUT/runtime-manifest.json" <<EOF
{
  "schema": 1,
  "artifact": "sd-cli",
  "platform": "linux-x86_64",
  "backend": "cpu-only",
  "stable_diffusion_cpp_commit": "$COMMIT",
  "ggml_native": false,
  "sha256": "$SHA"
}
EOF
printf '%s\n' "$VERSION" > "$OUT/sd-cli.version.txt"
printf '%s\n' "$DEVICES" > "$OUT/sd-cli.devices.txt"

tar -C "$OUT" -czf "$ROOT/$ARCHIVE_NAME" .
(
  cd "$ROOT"
  sha256sum "$ARCHIVE_NAME" > "$ARCHIVE_NAME.sha256"
)

echo "PORTABLE_RUNTIME_DIR=$OUT"
echo "PORTABLE_RUNTIME_ARCHIVE=$ROOT/$ARCHIVE_NAME"
echo 'RELEASE_PORTABLE_RUNTIME_BUILD=PASS'
