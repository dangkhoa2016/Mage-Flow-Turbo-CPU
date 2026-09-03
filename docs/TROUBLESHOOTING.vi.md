# Xử lý sự cố (Troubleshooting)

> 🌐 Ngôn ngữ / Language: **Tiếng Việt** | [English](TROUBLESHOOTING.md)

## Fail kiểm thử tĩnh / CI

- Chạy `python -m pytest tests/ -q`; nếu source thay đổi, sửa trước khi qualification thật rồi chạy lại CI và giữ run ID.
- `python scripts/publication/audit_public_surface.py --root .` phải in `PUBLICATION_SURFACE_AUDIT=PASS`; nó fail nếu core chứa đường dẫn Kaggle, có trọng số mô hình được track, README thiếu các mục bắt buộc, còn nhận diện sản phẩm cũ, hoặc workflow không dùng Actions v7.

## Build runtime

Kiểm tra log build của đúng commit đã pin và `sd-cli --version` / `--list-devices`. Không tự động nâng pin runtime. Lỗi Mage-Flow cụ thể cần đổi commit pin là quyết định thiết kế mới và phải qualification lại toàn bộ.

## CUDA

- Xác minh `nvidia-smi`, CUDA toolkit / `nvcc`, cờ build, `--list-devices`.
- Không bao giờ fallback âm thầm sang CPU khi yêu cầu CUDA; hãy fail closed.
- OOM trên T4: thử placement hỗn hợp tường minh (vd `diffusion=cuda0,te=cpu,vae=cpu`) trong khi giữ qualification deterministic và ghi lại topology; nếu stack tham chiếu không qualification nổi trên T4 theo cách có thể biện hộ, dừng lại và báo blocker thay vì tuyên bố hỗ trợ CUDA sai.

## Giải quyết mô hình

- Chỉ in đường dẫn/basename ứng viên và SHA thực tế so với mong đợi; không bao giờ bỏ qua kiểm tra SHA.
- Manifest cần đúng ba thành phần `diffusion`, `text_encoder`, `vae`, mỗi phần có SHA-256 hex 64 ký tự khớp file thực tế.
- Thiếu hoặc mơ hồ → fail closed.

## Lịch sử / lệch ngày

Không dùng GitHub Contents API cho commit (không đảm bảo ngày committer mong muốn). Dựng lại candidate history cục bộ và force-publish `main` đã xác minh đầy đủ.

## Bằng chứng bị lộ bí mật

Fail closed, tạo lại evidence đã khử nhạy cảm và xác minh trích xuất sạch phòng sạch (clean-room).
