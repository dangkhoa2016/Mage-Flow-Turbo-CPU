# Hướng dẫn Kaggle production demo notebook
[![CI](https://github.com/dangkhoa2016/Mage-Flow-Turbo-CPU/actions/workflows/ci.yml/badge.svg)](https://github.com/dangkhoa2016/Mage-Flow-Turbo-CPU/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/dangkhoa2016/Mage-Flow-Turbo-CPU?display_name=tag)](https://github.com/dangkhoa2016/Mage-Flow-Turbo-CPU/releases/tag/v1.0.0)
[![License](https://img.shields.io/github/license/dangkhoa2016/Mage-Flow-Turbo-CPU)](LICENSE)
![Kaggle](https://img.shields.io/badge/Kaggle-CPU%2FRAM--only-20BEFF?logo=kaggle&logoColor=white)

> 🌐 Language / Ngôn ngữ: [English](kaggle-production-demo-notebook.md) | **Tiếng Việt**

## Điều kiện
Internet ON, Accelerator=None và attach đủ bốn input Kaggle bắt buộc: public prebuilt CPU runtime dataset cộng ba variation canonical. Chạy `python3 scripts/configure_repo_origin.py --apply` trong Git clone thật và yêu cầu `python3 -m unittest -v tests.test_notebook_contract` PASS mà không bật chế độ cho placeholder.

## Contract Run All
Notebook hard-refresh source vào `/kaggle/working`; state mutable nằm tại `/kaggle/working/mage-flow-turbo-runtime`. Static test chạy trước build model runtime. Preflight xác minh toàn bộ SHA model và runtime commit. Notebook start REST localhost, chạy đúng một acceptance thật `demo` 512/seed42, hiển thị ảnh, thu evidence và stop service. Qualification này là PASS. 640/1024 và public mode không chạy nếu người dùng chưa bật.
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

