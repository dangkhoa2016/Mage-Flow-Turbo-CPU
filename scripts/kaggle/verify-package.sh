#!/usr/bin/env bash
set -Eeuo pipefail
A="${1:?archive required}"; S="${2:-$A.sha256}"; [[ -f "$A" && -f "$S" ]]
( cd "$(dirname "$A")" && sha256sum -c "$(basename "$S")" )
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
case "$A" in *.zip) unzip -q "$A" -d "$TMP";; *.tar.gz) tar -xzf "$A" -C "$TMP";; *) echo 'unsupported archive'; exit 2;; esac
! find "$TMP" -type f \( -name '*.gguf' -o -name '*.safetensors' -o -name '*.ckpt' -o -name '*.pt' -o -name '*.pth' -o -name '*.onnx' \) -print -quit | grep -q . || { echo 'PACKAGE_MODEL_WEIGHT_SCAN=FAIL'; exit 3; }
if [[ -f "$TMP/SOURCE-MANIFEST.sha256" ]]; then (cd "$TMP" && sha256sum -c SOURCE-MANIFEST.sha256 >/dev/null); echo 'SOURCE_MANIFEST_VERIFY=PASS'; fi
if [[ -f "$TMP/MANIFEST.sha256" ]]; then (cd "$TMP" && sha256sum -c MANIFEST.sha256 >/dev/null); echo 'EVIDENCE_MANIFEST_VERIFY=PASS'; fi
echo 'PACKAGE_REEXTRACT_VERIFY=PASS'
