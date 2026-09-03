# Kiến trúc production demo

> 🌐 Language / Ngôn ngữ: [English](production-demo.md) | **Tiếng Việt**

## Topology bắt buộc
`Notebook → 127.0.0.1:8090 REST → sd-cli → CPU`. REST coordinator chạy lâu dài; mỗi request ảnh được chấp nhận gọi command `sd-cli` đã freeze bằng `shell=False`. Inference single-flight.

## Topology public tùy chọn
`Internet → Cloudflare Quick Tunnel → 127.0.0.1:8091 Bearer gateway → 127.0.0.1:8090`. Cấm tunnel trỏ trực tiếp 8090. Public acceptance chỉ fetch artifact 512 đã có và không chạy inference mới. `AUTHENTICATED_PUBLIC_DEMO=NOT_RUN` vẫn hợp lệ cho core closeout.

## Chính sách profile
`demo=512` mặc định; `balanced=640` và `research=1024` opt-in. 768 đã validate kỹ thuật nhưng không là profile UX chính. Latency CPU lịch sử chỉ tham khảo (~4m43s ở 512, ~7m19s ở 640, ~20m02s ở 1024).

## Resource gate và timeout
Service fail trước khi khởi động `sd-cli` nếu không đạt resource gate dựa trên evidence. `demo` và `balanced` yêu cầu tối thiểu **16 GiB MemAvailable** và **2 GiB disk trống** trong workspace; `research` yêu cầu **20 GiB MemAvailable** và **3 GiB disk trống**. Hard timeout lần lượt là **900 s / 1200 s / 2700 s** cho `demo / balanced / research`. Khi timeout: SIGTERM → chờ 5 s → SIGKILL nếu cần; không tự retry.

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

