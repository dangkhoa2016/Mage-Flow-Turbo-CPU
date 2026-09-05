# Mage-Flow-Turbo-Native-Inference

[![CI](https://github.com/dangkhoa2016/Mage-Flow-Turbo-Native-Inference/actions/workflows/ci.yml/badge.svg)](https://github.com/dangkhoa2016/Mage-Flow-Turbo-Native-Inference/actions/workflows/ci.yml)
[![Native Runtime](https://github.com/dangkhoa2016/Mage-Flow-Turbo-Native-Inference/actions/workflows/native-runtime.yml/badge.svg)](https://github.com/dangkhoa2016/Mage-Flow-Turbo-Native-Inference/actions/workflows/native-runtime.yml)
[![Release](https://img.shields.io/github/v/release/dangkhoa2016/Mage-Flow-Turbo-Native-Inference)](https://github.com/dangkhoa2016/Mage-Flow-Turbo-Native-Inference/releases/tag/v1.0.0)
[![License](https://img.shields.io/github/license/dangkhoa2016/Mage-Flow-Turbo-Native-Inference)](LICENSE)

> 🌐 Ngôn ngữ / Language: **Tiếng Việt** | [English](README.md)

**Bộ công cụ suy luận native di động cho Mage-Flow-Turbo.** Repository này không định nghĩa mô hình mới và không huấn luyện hay fine-tune trọng số. Python đảm nhận cấu hình, kiểm tra, điều phối CLI/REST, vòng đời và thu thập evidence; việc suy luận mô hình thực tế do runtime native `stable-diffusion.cpp` (`sd-cli`) thực hiện.

```text
manifest → xác minh SHA-256 → runtime sd-cli đã pin
        → Mage-Flow-Turbo DiT Q8_0
        → Qwen3-VL-4B text encoder Q4_K_M
        → VAE riêng
        → Linux CPU hoặc NVIDIA CUDA cuda0
        → PNG + evidence có cấu trúc
```

## Reference stack chính xác

| Vai trò | Artifact chính xác | Định dạng / lượng tử hóa |
|---|---|---|
| Diffusion model | `Mage-Flow-Turbo-DiT-Q8_0.gguf` | GGUF Q8_0 |
| Text encoder | `Qwen3VL-4B-Instruct-Q4_K_M.gguf` | GGUF Q4_K_M |
| VAE | `diffusion_pytorch_model.safetensors` | SafeTensors |
| Runtime native | `stable-diffusion.cpp` `sd-cli` | commit đã pin `6b3edaaf32cc19e5bb2d819c788bd557eddc8eba` |

SHA-256 đông cứng được kiểm tra trước suy luận thật. Repository không chứa trọng số mô hình.

## Phạm vi qualification v1.0.0

v1.0.0 sử dụng đúng một Git source head và một hợp đồng model/runtime đã đông cứng. Các mục tiêu qualification bắt buộc gồm:

| Môi trường | Backend | Vai trò qualification |
|---|---|---|
| Linux x86-64 | CPU | release target bắt buộc |
| Linux + NVIDIA GPU | CUDA `cuda0` | release target bắt buộc |
| Notebook Kaggle CPU | CPU adapter | integration target bắt buộc |
| Notebook Kaggle T4/T4x2 | CUDA adapter `cuda0` trên physical GPU 0 | integration target bắt buộc |

Multi-GPU, Vulkan, Metal, ROCm, SYCL, Windows và các backend khác không nằm trong mục tiêu qualification của v1.0.0.

Kết quả PASS/FAIL cuối và evidence exact-head, bao gồm thời gian đo, telemetry RAM/VRAM, hash runtime binary, hash PNG acceptance, notebook đã chạy, release provenance và SHA-256 checksum, được phát hành cùng GitHub Release thay vì lưu như trạng thái động trong source tree.

## Vì sao dùng native inference?

Diffusion, text conditioning và giải mã VAE đều do `sd-cli` thực hiện; dự án không có vòng lặp suy luận PyTorch/Transformers. Python xác minh model, dựng subprocess argv tường minh với `shell=False`, giám sát tiến trình native và ghi evidence.

## Xác minh model stack

Model do người dùng cung cấp hoặc mount. Việc nạp dùng manifest JSON và fail closed nếu thiếu, mơ hồ hoặc hash không khớp.

```bash
mageflow-native verify --manifest configs/mage-flow-turbo-q8-reference.json
```

## Bắt đầu nhanh Linux CPU

```bash
python -m pip install -e .
mageflow-native runtime build --backend cpu
mageflow-native doctor --manifest configs/mage-flow-turbo-q8-reference.json
mageflow-native verify --manifest configs/mage-flow-turbo-q8-reference.json
mageflow-native generate \
  --manifest configs/mage-flow-turbo-q8-reference.json \
  --prompt "A small red fox sitting in a quiet green forest" \
  --output output
```

## Bắt đầu nhanh NVIDIA CUDA

```bash
python -m pip install -e .
mageflow-native runtime build --backend cuda
mageflow-native doctor \
  --manifest configs/mage-flow-turbo-q8-reference.json \
  --backend cuda0
mageflow-native generate \
  --manifest configs/mage-flow-turbo-q8-reference.json \
  --backend cuda0 \
  --prompt "A small red fox" \
  --output output
```

Qualification release dùng placement xác định (`cpu` hoặc `cuda0`), không dùng `auto` hay `--auto-fit`.

## CLI

```text
mageflow-native doctor
mageflow-native verify
mageflow-native generate
mageflow-native serve
mageflow-native runtime build --backend cpu|cuda
```

## REST API

Service tham chiếu bind vào `127.0.0.1` theo mặc định.

```text
GET  /healthz
GET  /readyz
GET  /v1/info
POST /v1/images/generate
GET  /v1/artifacts/<png>
```

Public exposure, nếu dùng, là phần gateway có authentication riêng và nằm ngoài qualification release.

## Kaggle

Kaggle là môi trường adapter/reference, không phải hard dependency của core. Logic khám phá input Kaggle nằm trong `integrations/kaggle/` và ánh xạ mounted inputs vào flow manifest/runtime chung. Xem [docs/kaggle.md](docs/kaggle.md) và [notebooks/kaggle-production-demo.ipynb](notebooks/kaggle-production-demo.ipynb).

## Tái lập và evidence

Qualification ghi exact Git head, runtime provenance, model hash, backend, prompt, seed, steps, CFG, threads, resolution, argv chính xác, stdout/stderr, exit code, wall time, peak memory telemetry và PNG identity. Evidence được sanitize và có thể clean-room verify.

Canonical release request:

```text
prompt  = A small red fox sitting in a quiet green forest, natural light, detailed photography.
size    = 512x512
seed    = 42
steps   = 4
CFG     = 1.0
threads = 4
```

Output CPU và CUDA có thể khác nhau ở mức byte do khác backend số học.

## Tài liệu

- [Kiến trúc](docs/architecture.md)
- [Model stack](docs/model-stack.md)
- [Linux cục bộ](docs/local-linux.md)
- [CUDA](docs/cuda.md)
- [Kaggle](docs/kaggle.md)
- [REST API](docs/REST-API.md)
- [Kiểm thử](docs/TESTING.md)
- [Xử lý sự cố](docs/TROUBLESHOOTING.md)
- [Đóng góp](.github/CONTRIBUTING.md)
- [Chính sách bảo mật](.github/SECURITY.md)

## Giấy phép

MIT License. Copyright © 2026 Đăng Khoa <i.am@dangkhoa.dev>.
