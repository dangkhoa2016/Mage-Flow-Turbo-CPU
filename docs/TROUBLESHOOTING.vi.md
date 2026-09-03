# Xử lý sự cố
[![CI](https://github.com/dangkhoa2016/Mage-Flow-Turbo-CPU/actions/workflows/ci.yml/badge.svg)](https://github.com/dangkhoa2016/Mage-Flow-Turbo-CPU/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/dangkhoa2016/Mage-Flow-Turbo-CPU?display_name=tag)](https://github.com/dangkhoa2016/Mage-Flow-Turbo-CPU/releases/tag/v1.0.0)
[![License](https://img.shields.io/github/license/dangkhoa2016/Mage-Flow-Turbo-CPU)](LICENSE)
![Kaggle](https://img.shields.io/badge/Kaggle-CPU%2FRAM--only-20BEFF?logo=kaggle&logoColor=white)

> 🌐 Language / Ngôn ngữ: [English](TROUBLESHOOTING.md) | **Tiếng Việt**

## Quy tắc retry
Trước khi `sd-cli` thật bắt đầu, có thể sửa lỗi bootstrap/path/port có recovery rõ ràng rồi chạy lại gate. Sau khi canonical real `sd-cli` đã start, **không tự chạy thêm ảnh thật**; giữ evidence và dừng để review trừ khi user chủ động mở acceptance run mới.

| Code | Recovery | Retry thật? |
|---|---|---|
| MODEL_MOUNT_MISSING | Sửa các Kaggle variation đã attach; chạy lại discovery/preflight. | Có nếu inference thật chưa start |
| MODEL_HASH_MISMATCH | Dừng; xác minh model/version, không thay quantization. | Không tự retry |
| VAE_ONLY_AMBIGUOUS | Detach VAE-only trùng để còn đúng một candidate. | Có trước inference |
| SD_CLI_MISSING | Chạy lại bootstrap CPU đúng pinned commit. | Có trước inference |
| RUNTIME_COMMIT_MISMATCH | Xóa riêng runtime build và build lại đúng commit. | Có trước inference |
| BUILD_FAILED | Xem CMake/compiler/disk log; không đổi upstream commit. | Có trước inference |
| INSUFFICIENT_MEM_AVAILABLE | Dừng process thừa hoặc tạo fresh CPU session. | Có trước inference |
| INSUFFICIENT_DISK | Xóa runtime/cache disposable, không sửa Kaggle input. | Có trước inference |
| PORT_ALREADY_IN_USE | Xác định owner; không tự kill process không thuộc project. | Có trước inference |
| SERVER_NOT_READY | Xem stderr/preflight; chưa gửi request generate. | Có trước inference |
| BUSY_SINGLE_FLIGHT | Chờ request hiện tại; không tạo backend song song. | Không phải retry request đang chạy |
| REQUEST_TIMEOUT | Giữ log/output và dừng review. | Không tự retry |
| SD_CLI_EXIT_NONZERO | Giữ stdout/stderr/result và phân loại lỗi. | Không tự retry |
| INVALID_PNG | Giữ bytes/log; không re-encode để “sửa”. | Không tự retry |
| ARTIFACT_HASH_MISMATCH | Giữ cả hai copy và metadata. | Không tự retry |
| ORPHAN_SD_CLI | Chỉ dừng child thuộc project sau khi verify PID/cmdline. | Không tự retry |
| CLOUDFLARED_MISSING | Nhánh optional: cung cấp `CLOUDFLARED_BIN` hoặc để public NOT_RUN. | Không cần inference |
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


## Lỗi evidence / Git provenance
| Mã | Cách xử lý | Có chạy lại inference thật? |
|---|---|---|
| ACTUAL_EVIDENCE_SEMANTIC_MISMATCH | Giữ nguyên evidence tree; đối chiếu preflight/local/request/result/telemetry. Không sửa evidence để tạo PASS giả. | Không cần inference |
| CANONICAL_RUN_EVIDENCE_MISSING | Sửa collector/source. Bắt buộc có request/stdout/stderr/telemetry/result. `argv.json` vẫn bị loại. | Không cần inference |
| REPO_ORIGIN_DISALLOWED_MARKER | Chỉ finalize origin từ URL GitHub chính thức thật; không gửi placeholder origin. | Không cần inference |
| REPO_ORIGIN_PENDING | Không tự bịa origin; chỉ finalize từ URL GitHub chính thức thật. | Không cần inference |
