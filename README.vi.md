# Mage-Flow-Turbo-Native-Inference

[![CI](https://github.com/dangkhoa2016/Mage-Flow-Turbo-Native-Inference/actions/workflows/ci.yml/badge.svg)](https://github.com/dangkhoa2016/Mage-Flow-Turbo-Native-Inference/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/dangkhoa2016/Mage-Flow-Turbo-Native-Inference)](LICENSE)

> 🌐 Ngôn ngữ / Language: **Tiếng Việt** | [English](README.md)

**Bộ công cụ suy luận native di động cho Mage-Flow-Turbo.** Đây không phải một mô hình mới và không huấn luyện hay tinh chỉnh gì. Python đảm nhận cấu hình, kiểm tra, điều phối CLI/REST, vòng đời và thu thập bằng chứng; việc suy luận mô hình thực tế do runtime native `stable-diffusion.cpp` (`sd-cli`) thực hiện.

## Chạy thực tế là gì?

```text
manifest → xác minh SHA-256 → runtime manager (sd-cli)
        → Mage-Flow-Turbo DiT (Q8_0) + Qwen3-VL-4B text encoder + VAE riêng
        → Linux CPU hoặc NVIDIA CUDA (cuda0)
        → ảnh PNG
```

## Các thành phần mô hình chính xác

| Vai trò | Tệp chính xác | Định dạng / lượng tử hóa |
|---|---|---|
| Diffusion | `Mage-Flow-Turbo-DiT-Q8_0.gguf` | GGUF Q8_0 |
| Text encoder / LLM | `Qwen3VL-4B-Instruct-Q4_K_M.gguf` | GGUF Q4_K_M |
| VAE | `diffusion_pytorch_model.safetensors` | SafeTensors |
| Engine native | `stable-diffusion.cpp` `sd-cli` | C/C++ (commit `6b3edaaf…`) |

Cả ba thành phần đều bắt buộc. SHA-256 đông cứng và runtime được xác minh trước khi suy luận thật. **Không dùng vòng lặp suy luận PyTorch/Transformers.**

## Trạng thái qualification v1.0.0

| Môi trường | Backend | Trạng thái |
|---|---|---|
| Linux x86-64 | CPU | Đang chờ qualification |
| Linux + NVIDIA GPU | CUDA (`cuda0`) | Đang chờ qualification |
| Notebook Kaggle CPU | CPU adapter | Đang chờ qualification |
| Notebook Kaggle T4/T4x2 | CUDA adapter (`cuda0`) | Đang chờ qualification |

Các trạng thái trên chỉ được chuyển sang `qualified` sau khi exact public source head vượt qua gate tương ứng và evidence đã được xác minh.

## Tại sao không dùng PyTorch?

Diffusion, điều kiện văn bản và giải mã VAE đều do runtime native `sd-cli` thực hiện. Python chỉ kiểm tra cấu hình và mô hình, dựng argv subprocess tường minh (`shell=False`), giám sát tiến trình và thu thập bằng chứng.

## Nạp mô hình và xác minh SHA

Tệp mô hình do người dùng cung cấp hoặc mount; repository không chứa trọng số mô hình:

```bash
mageflow-native verify --manifest configs/mage-flow-turbo-q8-reference.json
```

Thiếu hoặc mơ hồ một thành phần sẽ **fail closed**.

## Bắt đầu nhanh Linux CPU

```bash
python -m pip install -e .
mageflow-native runtime build --backend cpu
mageflow-native verify --manifest configs/mage-flow-turbo-q8-reference.json
mageflow-native generate --manifest configs/mage-flow-turbo-q8-reference.json \
    --prompt "Một con cáo nhỏ trong rừng xanh yên tĩnh" --output output
```

## Bắt đầu nhanh NVIDIA CUDA

```bash
python -m pip install -e .
mageflow-native runtime build --backend cuda
mageflow-native generate --manifest configs/mage-flow-turbo-q8-reference.json \
    --backend cuda0 --prompt "Một con cáo nhỏ" --output output
```

Việc qualification chỉ dùng placement xác định (`cpu`, `cuda0`), không dùng `auto` hay `--auto-fit`.

## CLI và REST

```text
mageflow-native doctor | verify | generate | serve | runtime build --backend cpu|cuda
GET  /healthz   GET /readyz   GET /v1/info
POST /v1/images/generate      GET /v1/artifacts/<png>
```

## Kaggle

Kaggle là môi trường **adapter/tham chiếu**, không phải runtime bắt buộc. Qualification live CPU/CUDA cuối cho v1.0.0 hiện đang chờ thực hiện. Mã dành riêng cho Kaggle nằm trong `integrations/kaggle/` và chỉ khám phá input đã mount rồi tạo manifest chung; core chung sau đó chạy trên CPU hoặc CUDA. Xem [docs/kaggle.md](docs/kaggle.md).

## Tài liệu

- [Kiến trúc](docs/architecture.md)
- [Model stack](docs/model-stack.md)
- [Linux cục bộ](docs/local-linux.md)
- [CUDA](docs/cuda.md)
- [REST API](docs/REST-API.md)
- [Kiểm thử](docs/TESTING.md)
- [Xử lý sự cố](docs/TROUBLESHOOTING.md)

## Giấy phép

MIT License. Copyright © 2026 Đăng Khoa <i.am@dangkhoa.dev>.
