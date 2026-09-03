# Lịch sử thay đổi
[![CI](https://github.com/dangkhoa2016/Mage-Flow-Turbo-CPU/actions/workflows/ci.yml/badge.svg)](https://github.com/dangkhoa2016/Mage-Flow-Turbo-CPU/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/dangkhoa2016/Mage-Flow-Turbo-CPU?display_name=tag)](https://github.com/dangkhoa2016/Mage-Flow-Turbo-CPU/releases/tag/v1.0.0)
[![License](https://img.shields.io/github/license/dangkhoa2016/Mage-Flow-Turbo-CPU)](LICENSE)
![Kaggle](https://img.shields.io/badge/Kaggle-CPU%2FRAM--only-20BEFF?logo=kaggle&logoColor=white)

> 🌐 Language / Ngôn ngữ: [English](CHANGELOG.md) | **Tiếng Việt**

## v1.0.0 — 2026-09-02
- Bản phát hành công khai. Qualification fresh Kaggle Restart Session → Run All là PASS; toàn bộ bộ contract static đạt PASS.
- Lịch sử Git trên nhánh `main` với identity author/committer chuẩn; `master` cũ được xóa rõ ràng sau khi đã tạo backup bundle bảo vệ.
- Thay dependency VAE variation nặng bằng input VAE-only riêng đã được readback/hash độc lập.
- Thêm resolver input động dựa SHA, không fallback sang full variation cũ.
- Thêm REST local theo profile, notebook repository-first song ngữ, authenticated gateway tùy chọn, evidence/CI contract và chính sách đúng một real acceptance.
- Thêm evidence semantics derive/cross-check từ các evidence file thực tế, lưu seed/exit code/elapsed time, và tiếp tục loại raw `argv.json` khỏi publication evidence.
- Bổ sung actual-evidence mutation matrix 16 case bên cạnh contract negative matrix 30 case đã đóng băng.
- Phase E/E.1 giữ freeze như evidence lịch sử; PyTorch v0.1.2 chỉ còn là reference.
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
