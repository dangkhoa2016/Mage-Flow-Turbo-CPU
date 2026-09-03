# Mage-Flow-Turbo-CPU

[![CI](https://github.com/dangkhoa2016/Mage-Flow-Turbo-CPU/actions/workflows/ci.yml/badge.svg)](https://github.com/dangkhoa2016/Mage-Flow-Turbo-CPU/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/dangkhoa2016/Mage-Flow-Turbo-CPU?display_name=tag)](https://github.com/dangkhoa2016/Mage-Flow-Turbo-CPU/releases/tag/v1.0.0)
[![License](https://img.shields.io/github/license/dangkhoa2016/Mage-Flow-Turbo-CPU)](LICENSE)
![Kaggle](https://img.shields.io/badge/Kaggle-CPU%2FRAM--only-20BEFF?logo=kaggle&logoColor=white)


> 🌐 Language / Ngôn ngữ: [English](README.md) | **Tiếng Việt**

Dự án demo **Mage-Flow-Turbo chạy CPU/RAM-only trên Kaggle** theo hướng tái lập được, sử dụng runtime `stable-diffusion.cpp` đã pin và các model input GGUF. Repository cung cấp REST local, notebook Kaggle fresh-session, resource gate, evidence collection và gateway public có xác thực tùy chọn quanh một inference contract đã freeze.

## Dự án chứng minh gì

- chạy Mage-Flow-Turbo bằng CPU trên Kaggle với `Accelerator=None`;
- runtime `sd-cli` portable đã verify, có source-build fallback;
- lifecycle REST local xác định trên `127.0.0.1:8090`;
- đúng một canonical real acceptance trong luồng qualification mặc định;
- UX notebook song ngữ English/Tiếng Việt và transport UTF-8;
- Quick Tunnel có xác thực tùy chọn mà không expose trực tiếp backend;
- kiểm tra input, evidence packaging và CI theo fail-closed contract.

Đây là dự án phục vụ reproducibility và integration. Repository **không** tuyên bố CPU production latency SLA và không benchmark chất lượng hình ảnh tiếng Việt.

## Chạy nhanh trên Kaggle

1. Tạo Kaggle Notebook mới với **Internet ON** và **Accelerator=None**.
2. Attach bốn public input bắt buộc:
   - portable `stable-diffusion.cpp` CPU runtime dataset;
   - Mage-Flow-Turbo DiT `q8-0`;
   - variation VAE-only riêng;
   - Qwen `q4-k-m` GGUF input.
3. Import `notebooks/kaggle-cpu-production-demo.ipynb`.
4. Chọn **Restart Session → Run All**.
5. Giữ mặc định của release:

```text
RUN_LIVE_DEMO=True
ENABLE_PUBLIC_TUNNEL=False
RUN_OPTIONAL_USER_GENERATION=False
MAGE_PROFILE="demo"
```

Profile qualification mặc định là 512×512. Profile 640 là tùy chọn; 1024 dành cho research/experimental.

## REST surface

```text
GET  /healthz
GET  /readyz
GET  /v1/info
POST /v1/images/generate
GET  /v1/artifacts/<png>
```

Inference backend chỉ bind loopback. Public path tùy chọn đi qua gateway riêng có xác thực.

## Frozen technical contract

```text
stable-diffusion.cpp = 6b3edaaf32cc19e5bb2d819c788bd557eddc8eba
DiT Q8 SHA256         = 4c3dafc143ee64121692b6b63563a4f5288bf6183c4870e1d65f1566519ba7f0
Qwen Q4_K_M SHA256    = 66358cb18bb6b3b1b6675aa412c7a88ef01d228f481184d13668e5201c730a0a
VAE-only SHA256       = 34e076dc1e8a15321e1e07be5111d59cf16dd10b804b7c7e20b4de29013427e0
VAE package            = pytorch/vae-only
profiles               = demo 512 | balanced 640 | research 1024
backend                 = 127.0.0.1:8090 CPU only
auth gateway            = 127.0.0.1:8091 optional
steps / CFG / threads   = 4 / 1.0 / 4
```

Public prebuilt runtime dataset đã verify:

```text
dangkhoa2016/stable-diffusion-cpp-6b3edaa-portable-cpu-runtime
sd-cli SHA256 = 7539d90b99eaf2b6279eec4f9006a68ae53e87bfe0c9c325ff3f329220468a5c
```

## Trạng thái release

`v1.0.0` là public release đầu tiên. Release contract cuối yêu cầu toàn bộ static suite PASS và một lần qualification fresh Kaggle **Restart Session → Run All** trên đúng source tree đã publish.

## Cấu trúc repository

```text
app/                    REST local và inference orchestration
notebooks/              Kaggle production demo notebook
runtime/                provenance của runtime đã pin
scripts/                verification và packaging utilities
scripts/kaggle/         Kaggle lifecycle và acceptance utilities
tests/                  static và contract tests
.github/                 CI và community health files
docs/                    tài liệu song ngữ cho người dùng
```

## Tài liệu

- [Kaggle production demo](docs/kaggle-production-demo-notebook.vi.md)
- [Testing](docs/TESTING.vi.md)
- [Troubleshooting](docs/TROUBLESHOOTING.vi.md)
- [Release notes](docs/RELEASE-NOTES-v1.0.0.vi.md)
- [Đóng góp](.github/CONTRIBUTING.md)
- [Security policy](.github/SECURITY.md)

## Giấy phép

MIT License. Copyright © 2026 Đăng Khoa <i.am@dangkhoa.dev>.
