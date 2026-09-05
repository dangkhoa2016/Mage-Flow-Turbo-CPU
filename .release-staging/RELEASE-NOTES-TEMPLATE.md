# Mage-Flow-Turbo-Native-Inference v1.0.0

## English

`v1.0.0` is the first public release of **Mage-Flow-Turbo-Native-Inference**, a portable native inference stack for Mage-Flow-Turbo built around `stable-diffusion.cpp/sd-cli`, explicit CPU/CUDA backends, frozen model identities, release-grade provenance, and Kaggle reference workflows.

### Qualified source

- Git commit: `b9042c743aa925042349af3cf6fcf37dc455af6e`
- `stable-diffusion.cpp`: `6b3edaaf32cc19e5bb2d819c788bd557eddc8eba`
- `ggml`: `e20c3a14aa70ee84ca58499814206dd08d8026bc`

The `v1.0.0` annotated tag points directly to the exact qualified Git commit above.

### Frozen model identities

- Mage-Flow-Turbo DiT Q8_0: `4c3dafc143ee64121692b6b63563a4f5288bf6183c4870e1d65f1566519ba7f0`
- Qwen3-VL-4B-Instruct Q4_K_M: `66358cb18bb6b3b1b6675aa412c7a88ef01d228f481184d13668e5201c730a0a`
- Mage-Flow-Turbo VAE: `34e076dc1e8a15321e1e07be5111d59cf16dd10b804b7c7e20b4de29013427e0`

### Canonical qualification request

- Prompt: `A small red fox sitting in a quiet green forest, natural light, detailed photography.`
- Size: `512×512`
- Seed: `42`
- Steps: `4`
- CFG: `1.0`
- Threads: `4`

### Fresh CPU qualification — PASS

- Exact source HEAD: `b9042c743aa925042349af3cf6fcf37dc455af6e`
- Backend: explicit `cpu`
- Fresh-session proof: PASS
- Exactly one real generation: PASS
- Elapsed: `290540 ms` (`290.54 s`, about `4m 50.54s`)
- Peak `sd-cli` RSS: `8465892 KiB` (about `8.07 GiB`)
- GPU/VRAM activity: none / `0`
- Pinned CPU `sd-cli` SHA-256: `7539d90b99eaf2b6279eec4f9006a68ae53e87bfe0c9c325ff3f329220468a5c`
- Acceptance PNG SHA-256: `c67f3aa4c475f33f5fcecb58392b0a21d1cd82d4d545d5f6e48f59e6a585d819`
- Evidence archive SHA-256: `541f0a11097310ac1097e562fa3aee1f313fb9013f09ca533e69d50567578a10`

### Fresh CUDA0 qualification — PASS

- Exact source HEAD: `b9042c743aa925042349af3cf6fcf37dc455af6e`
- Physical device: Tesla T4 GPU0
- Logical backend: explicit `cuda0`
- `CUDA_VISIBLE_DEVICES=0`
- `SD_CUDA=ON`
- `GGML_CUDA_NO_VMM=ON`
- Historical `CUDA::cuda_driver` configure failure: absent
- Fresh-session proof: PASS
- Exactly one real generation: PASS
- Second real generation: **NOT RUN**
- Elapsed: `8217 ms` (`8.217 s`)
- Peak `sd-cli` RSS: `2288312 KiB` (about `2.18 GiB`)
- Peak GPU memory: `8196 MiB`
- Fresh CUDA `sd-cli` SHA-256: `ab70ee2e9e6774dcfe5b9b0b964d0cee6f661c844dfa386058f0d2b6b8f146fa`
- Acceptance PNG SHA-256: `8df6d4f856f25aa2250d9c7865e2b91268aefc0d6c441b472eb4c886397c6452`
- Evidence archive SHA-256: `2302dc89416afb1658ba38fa496f8ae71afe1f080ddb54249adb00e94b5f0d44`
- CPU-to-CUDA0 wall-time speedup for the canonical request: about `35.36×`

The native CUDA generation itself succeeded. The original qualification harness then stopped because it incorrectly required `stderr` to be empty even though pinned GGML writes its normal CUDA device-discovery INFO lines there. A zero-inference forensic salvage validated a strict two-line GGML INFO allowlist, preserved the original harness failure, verified the successful native result and positive GPU telemetry, and proved that no second generation was executed.

### GitHub Actions gates

- CI on qualified `main`: run `33958730139` — PASS
- Native Runtime on qualified `main`: run `33958730991` — PASS
- CI on `v1.0.0` tag: run `__CI_TAG_RUN_ID__` — PASS
- Native Runtime on `v1.0.0` tag: run `__NATIVE_TAG_RUN_ID__` — PASS

### Evidence and reproducibility

This release publishes the CPU/CUDA evidence archives, archive sidecars, acceptance PNGs, executed qualification notebooks, the zero-inference CUDA salvage record, bilingual runnable qualification notebooks, release provenance, tag message, and a `SHA256SUMS` file covering every custom release asset except `SHA256SUMS` itself.

No model weights are included in the Git repository or GitHub Release assets.

The publication-quality CUDA0 runnable notebook includes the strict GGML INFO `stderr` allowlist proven by the forensic run, preventing the already-understood harness false failure while keeping every unexpected `stderr` line as a hard failure.

### Scope

Qualified for:

- Linux x86-64 CPU native inference
- NVIDIA CUDA `cuda0`
- Kaggle CPU adapter
- Kaggle T4/T4x2 adapter with physical GPU0 / logical `cuda0`

This release does not claim bit-identical output across CPU and CUDA backends. Each backend is independently qualified against its own evidence and acceptance image.

---

## Tiếng Việt

`v1.0.0` là bản phát hành công khai đầu tiên của **Mage-Flow-Turbo-Native-Inference**, một native inference stack portable cho Mage-Flow-Turbo dựa trên `stable-diffusion.cpp/sd-cli`, backend CPU/CUDA tường minh, model identity đóng băng, provenance cấp release và các workflow tham chiếu cho Kaggle.

### Source đã được kiểm định

- Git commit: `b9042c743aa925042349af3cf6fcf37dc455af6e`
- `stable-diffusion.cpp`: `6b3edaaf32cc19e5bb2d819c788bd557eddc8eba`
- `ggml`: `e20c3a14aa70ee84ca58499814206dd08d8026bc`

Annotated tag `v1.0.0` trỏ trực tiếp tới đúng Git commit đã được kiểm định ở trên.

### Model identities đã đóng băng

- Mage-Flow-Turbo DiT Q8_0: `4c3dafc143ee64121692b6b63563a4f5288bf6183c4870e1d65f1566519ba7f0`
- Qwen3-VL-4B-Instruct Q4_K_M: `66358cb18bb6b3b1b6675aa412c7a88ef01d228f481184d13668e5201c730a0a`
- Mage-Flow-Turbo VAE: `34e076dc1e8a15321e1e07be5111d59cf16dd10b804b7c7e20b4de29013427e0`

### Canonical qualification request

- Prompt: `A small red fox sitting in a quiet green forest, natural light, detailed photography.`
- Kích thước: `512×512`
- Seed: `42`
- Steps: `4`
- CFG: `1.0`
- Threads: `4`

### Fresh CPU qualification — PASS

- Exact source HEAD: `b9042c743aa925042349af3cf6fcf37dc455af6e`
- Backend: explicit `cpu`
- Fresh-session proof: PASS
- Đúng một real generation: PASS
- Thời gian: `290540 ms` (`290.54 s`, khoảng `4 phút 50.54 giây`)
- Peak `sd-cli` RSS: `8465892 KiB` (khoảng `8.07 GiB`)
- GPU/VRAM activity: không / `0`
- Pinned CPU `sd-cli` SHA-256: `7539d90b99eaf2b6279eec4f9006a68ae53e87bfe0c9c325ff3f329220468a5c`
- Acceptance PNG SHA-256: `c67f3aa4c475f33f5fcecb58392b0a21d1cd82d4d545d5f6e48f59e6a585d819`
- Evidence archive SHA-256: `541f0a11097310ac1097e562fa3aee1f313fb9013f09ca533e69d50567578a10`

### Fresh CUDA0 qualification — PASS

- Exact source HEAD: `b9042c743aa925042349af3cf6fcf37dc455af6e`
- Physical device: Tesla T4 GPU0
- Logical backend: explicit `cuda0`
- `CUDA_VISIBLE_DEVICES=0`
- `SD_CUDA=ON`
- `GGML_CUDA_NO_VMM=ON`
- Historical `CUDA::cuda_driver` configure failure: không xuất hiện
- Fresh-session proof: PASS
- Đúng một real generation: PASS
- Real generation lần hai: **KHÔNG CHẠY**
- Thời gian: `8217 ms` (`8.217 s`)
- Peak `sd-cli` RSS: `2288312 KiB` (khoảng `2.18 GiB`)
- Peak GPU memory: `8196 MiB`
- Fresh CUDA `sd-cli` SHA-256: `ab70ee2e9e6774dcfe5b9b0b964d0cee6f661c844dfa386058f0d2b6b8f146fa`
- Acceptance PNG SHA-256: `8df6d4f856f25aa2250d9c7865e2b91268aefc0d6c441b472eb4c886397c6452`
- Evidence archive SHA-256: `2302dc89416afb1658ba38fa496f8ae71afe1f080ddb54249adb00e94b5f0d44`
- Tăng tốc wall-time CPU → CUDA0 trên canonical request: khoảng `35.36×`

Native CUDA generation đã thành công. Original qualification harness dừng sau đó vì yêu cầu sai rằng `stderr` phải rỗng hoàn toàn, trong khi GGML đã pin ghi các dòng CUDA device-discovery INFO bình thường vào `stderr`. Zero-inference forensic salvage đã xác minh strict allowlist đúng hai dòng GGML INFO, giữ nguyên original harness failure, xác minh native result thành công cùng GPU telemetry dương và chứng minh không chạy generation lần hai.

### GitHub Actions gates

- CI trên qualified `main`: run `33958730139` — PASS
- Native Runtime trên qualified `main`: run `33958730991` — PASS
- CI trên tag `v1.0.0`: run `__CI_TAG_RUN_ID__` — PASS
- Native Runtime trên tag `v1.0.0`: run `__NATIVE_TAG_RUN_ID__` — PASS

### Evidence và khả năng tái kiểm chứng

Release này công bố CPU/CUDA evidence archives, archive sidecars, acceptance PNGs, executed qualification notebooks, zero-inference CUDA salvage record, bilingual runnable qualification notebooks, release provenance, tag message và file `SHA256SUMS` bao phủ toàn bộ custom release assets ngoại trừ chính `SHA256SUMS`.

Không có model weights trong Git repository hoặc GitHub Release assets.

Publication-quality CUDA0 runnable notebook đã tích hợp strict GGML INFO `stderr` allowlist được chứng minh từ forensic run, tránh false failure đã hiểu rõ nhưng vẫn coi mọi `stderr` line bất ngờ là hard failure.

### Phạm vi

Đã kiểm định cho:

- Linux x86-64 CPU native inference
- NVIDIA CUDA `cuda0`
- Kaggle CPU adapter
- Kaggle T4/T4x2 adapter với physical GPU0 / logical `cuda0`

Release không tuyên bố CPU và CUDA phải tạo output byte-identical. Mỗi backend được kiểm định độc lập bằng evidence và acceptance image riêng.
