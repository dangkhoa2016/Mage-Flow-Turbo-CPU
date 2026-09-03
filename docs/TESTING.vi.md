# Kiểm thử
[![CI](https://github.com/dangkhoa2016/Mage-Flow-Turbo-CPU/actions/workflows/ci.yml/badge.svg)](https://github.com/dangkhoa2016/Mage-Flow-Turbo-CPU/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/dangkhoa2016/Mage-Flow-Turbo-CPU?display_name=tag)](https://github.com/dangkhoa2016/Mage-Flow-Turbo-CPU/releases/tag/v1.0.0)
[![License](https://img.shields.io/github/license/dangkhoa2016/Mage-Flow-Turbo-CPU)](LICENSE)
![Kaggle](https://img.shields.io/badge/Kaggle-CPU%2FRAM--only-20BEFF?logo=kaggle&logoColor=white)

> 🌐 Language / Ngôn ngữ: [English](TESTING.md) | **Tiếng Việt**

## Gate rẻ chạy trước
Chạy `python3 -m unittest discover -s tests -v`, `python3 -m py_compile app/*.py scripts/kaggle/*.py`, shell syntax check, validate JSON notebook và negative matrix 30 case trước mọi inference thật. Fake REST test bao phủ UTF-8, profile routing, single-flight và artifact continuity.

## Live gate
Chỉ final Git HEAD đã publish mới đủ điều kiện. Fresh Kaggle Restart Session → Run All đã hoàn thành đúng một acceptance thật 512 canonical và là PASS. Không tự retry sau khi `sd-cli` bắt đầu. Nếu sửa source sau live acceptance thì acceptance đó không còn đại diện cho source mới.
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


## Gate bản phát hành
Bộ kiểm thử đã phát hành đạt:

```text
static tests                       = PASS
contract negative matrix           = 30/30 EXPECTED_FAILURE
actual-evidence mutation matrix    = 16/16 EXPECTED_FAILURE
canonical run evidence archive     = request/stdout/stderr/telemetry/result
raw argv publication               = FORBIDDEN
branch                             = main
public author + committer          = Đăng Khoa <i.am@dangkhoa.dev>
```

`verify_evidence.py` xem preflight/local/run evidence và PNG thực tế là nguồn dữ liệu có thẩm quyền rồi cross-check với `contract.json`; chỉ rebuild manifest không thể làm một evidence tree sai semantic trở thành PASS.
