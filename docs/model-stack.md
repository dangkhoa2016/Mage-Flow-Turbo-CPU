# Model stack

The v1.0.0 reference model contract is frozen:

| Role | Exact artifact | Format / quantization | Canonical source hint |
|---|---|---|---|
| Diffusion model | `Mage-Flow-Turbo-DiT-Q8_0.gguf` | GGUF Q8_0 | `mage-flow-community-mage-flow-turbo/gguf/q8-0` |
| Text encoder / LLM | `Qwen3VL-4B-Instruct-Q4_K_M.gguf` | GGUF Q4_K_M | `qwen-qwen3-vl-4b-instruct-gguf/gguf/q4-k-m` |
| VAE | `diffusion_pytorch_model.safetensors` | SafeTensors | `mage-flow-community-mage-flow-turbo/pytorch/vae-only` |
| Native inference engine | `stable-diffusion.cpp` | C/C++ native | pinned commit `6b3edaaf32cc19e5bb2d819c788bd557eddc8eba` |
| Executable | `sd-cli` | native executable | built or supplied |

Frozen SHA-256 identities:

- DiT: `4c3dafc143ee64121692b6b63563a4f5288bf6183c4870e1d65f1566519ba7f0`
- Qwen: `66358cb18bb6b3b1b6675aa412c7a88ef01d228f481184d13668e5201c730a0a`
- VAE: `34e076dc1e8a15321e1e07be5111d59cf16dd10b804b7c7e20b4de29013427e0`

## Why three components?

Mage-Flow-Turbo separates the diffusion transformer (DiT), the text/LLM conditioner (Qwen3-VL-4B) and the image decoder (VAE). `sd-cli` needs all three to produce an image. The reference manifest (see `configs/mage-flow-turbo-q8-reference.json`) lists each with its format, quantization and frozen SHA-256.

## Verification

Before real inference the core loads the JSON manifest, resolves every component path, and SHA-256 hashes each file. A missing, ambiguous, or mismatched component fails closed. No inference starts until all three model identities and the pinned runtime identity are verified.
