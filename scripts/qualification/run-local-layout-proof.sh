#!/usr/bin/env bash
set -Eeuo pipefail
# Generic local-layout portability proof.
# Runs generic doctor + verify under a non-Kaggle path layout with an explicit manifest.
usage() {
  echo "usage: $0 --dit <path> --qwen <path> --vae <path> [--runtime-root <dir>]"
  exit 2
}
DIT=""; QWEN=""; VAE=""; RUNTIME_ROOT="${MAGE_RUNTIME_ROOT:-/tmp/mageflow-native-portability-proof/runtime}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dit) DIT="$2"; shift 2;;
    --qwen) QWEN="$2"; shift 2;;
    --vae) VAE="$2"; shift 2;;
    --runtime-root) RUNTIME_ROOT="$2"; shift 2;;
    *) usage;;
  esac
done
[[ -n "$DIT" && -n "$QWEN" && -n "$VAE" ]] || usage

PROOF=/tmp/mageflow-native-portability-proof
MODELS="$PROOF/models"
rm -rf "$PROOF"
mkdir -p "$MODELS"
ln -s "$DIT"  "$MODELS/Mage-Flow-Turbo-DiT-Q8_0.gguf"
ln -s "$QWEN" "$MODELS/Qwen3VL-4B-Instruct-Q4_K_M.gguf"
ln -s "$VAE"  "$MODELS/diffusion_pytorch_model.safetensors"

MANIFEST="$(mktemp)"
cat > "$MANIFEST" <<EOF
{
  "schema_version": 1,
  "model_family": "Mage-Flow-Turbo",
  "components": {
    "diffusion": { "path": "$MODELS/Mage-Flow-Turbo-DiT-Q8_0.gguf", "sha256": "$(sha256sum "$DIT" | awk '{print $1}')", "format": "gguf", "quantization": "Q8_0" },
    "text_encoder": { "path": "$MODELS/Qwen3VL-4B-Instruct-Q4_K_M.gguf", "sha256": "$(sha256sum "$QWEN" | awk '{print $1}')", "format": "gguf", "quantization": "Q4_K_M" },
    "vae": { "path": "$MODELS/diffusion_pytorch_model.safetensors", "sha256": "$(sha256sum "$VAE" | awk '{print $1}')", "format": "safetensors" }
  }
}
EOF

export MAGE_RUNTIME_ROOT="$RUNTIME_ROOT"
echo "LOCAL_LAYOUT_PROOF=START"
mageflow-native doctor --manifest "$MANIFEST" --json
mageflow-native verify --manifest "$MANIFEST" --backend cpu --json
echo "LOCAL_LAYOUT_PROOF=PASS"
