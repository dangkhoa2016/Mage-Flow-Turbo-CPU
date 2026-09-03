# Mage-Flow-Turbo-CPU Ghi chú phát hành v1.0.0
[![CI](https://github.com/dangkhoa2016/Mage-Flow-Turbo-CPU/actions/workflows/ci.yml/badge.svg)](https://github.com/dangkhoa2016/Mage-Flow-Turbo-CPU/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/dangkhoa2016/Mage-Flow-Turbo-CPU?display_name=tag)](https://github.com/dangkhoa2016/Mage-Flow-Turbo-CPU/releases/tag/v1.0.0)
[![License](https://img.shields.io/github/license/dangkhoa2016/Mage-Flow-Turbo-CPU)](LICENSE)
![Kaggle](https://img.shields.io/badge/Kaggle-CPU%2FRAM--only-20BEFF?logo=kaggle&logoColor=white)

> 🌐 Language / Ngôn ngữ: [English](RELEASE-NOTES-v1.0.0.md) | **Tiếng Việt**

## Nội dung

Mage-Flow-Turbo-CPU là demo production-oriented CPU/RAM-only trên Kaggle theo mô hình repository-first, xây dựng trên stack stable-diffusion.cpp + GGUF đã freeze. v1.0.0, phát hành ngày 2026-09-04, là bản phát hành công khai đầu tiên của dòng sản phẩm này.

## Điểm nổi bật

- Lifecycle REST local CPU-only portable với packaging fail-closed.
- Xác minh chính xác danh tính input theo frozen technical contract.
- Đúng một acceptance thật 512 từ fresh Kaggle notebook (không tự retry sau khi `sd-cli` chạy).
- Runtime CPU prebuilt đã xác minh từ public Kaggle dataset, có fallback source build cho chế độ public `auto` và fail-closed `prebuilt` cho chế độ acceptance.
- Quick Tunnel có Bearer auth là nhánh tùy chọn, không expose trực tiếp backend.
- UX song ngữ English/Tiếng Việt và transport UTF-8.
- Evidence đã sanitize và bộ contract static đầy đủ cùng negative matrix contract và actual-evidence.

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

## Public runtime dataset

`dangkhoa2016/stable-diffusion-cpp-6b3edaa-portable-cpu-runtime`

`sd-cli` SHA-256 đã xác minh:

`7539d90b99eaf2b6279eec4f9006a68ae53e87bfe0c9c325ff3f329220468a5c`

## Bắt đầu nhanh

Attach đủ bốn input Kaggle bắt buộc (public prebuilt CPU runtime dataset + DiT q8-0 + VAE-only + Qwen q4-k-m), finalize GitHub origin, import `notebooks/kaggle-cpu-production-demo.ipynb`, chọn **Restart Session -> Run All** và giữ mặc định.

`RUN_LIVE_DEMO=True`, `ENABLE_PUBLIC_TUNNEL=False`, `RUN_OPTIONAL_USER_GENERATION=False`, `MAGE_PROFILE="demo"`.

## Baseline

v1.0.0 được phát hành từ cây mã nguồn đã qualification cuối cùng trên `main`, đánh dấu bằng tag annotated `v1.0.0`. Bản này gồm tài liệu publication-facing, release publication contract tests, tag annotated và GitHub Release. PNG 512 canonical và evidence production đã sanitize được tạo bởi đúng một lần qualification Kaggle `Restart Session -> Run All` trên đúng cây mã nguồn đó; SHA-256 của chúng được ghi trong evidence archive để kiểm tra độc lập.

## License

Bản phát hành này được cấp phép theo **MIT License**. Bản quyền (c) 2026 `Đăng Khoa <i.am@dangkhoa.dev>`. Xem file `LICENSE` để có đầy đủ nội dung. Chủ sở hữu đã chọn MIT một cách tường minh; license không được suy đoán từ các component upstream.
