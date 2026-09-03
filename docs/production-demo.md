# Production demo architecture

> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](production-demo.vi.md)

## Required topology
`Notebook → 127.0.0.1:8090 REST → sd-cli → CPU`. The REST coordinator is persistent; each accepted image request starts the frozen `sd-cli` command with `shell=False`. Generation is single-flight.

## Optional public topology
`Internet → Cloudflare Quick Tunnel → 127.0.0.1:8091 Bearer gateway → 127.0.0.1:8090`. Tunnel targeting 8090 directly is forbidden. Public acceptance fetches the existing 512 artifact and performs zero new inference. `AUTHENTICATED_PUBLIC_DEMO=NOT_RUN` is valid for core closeout.

## Product policy
`demo=512` is default; `balanced=640` and `research=1024` are opt-in. 768 remains technically validated but is not a primary UX profile. Historical CPU observations are informative only (~4m43s at 512, ~7m19s at 640, ~20m02s at 1024).

## Resource and timeout admission
The service fails before starting `sd-cli` when the evidence-backed resource gate is not met. `demo` and `balanced` require at least **16 GiB MemAvailable** and **2 GiB workspace free disk**; `research` requires **20 GiB MemAvailable** and **3 GiB free disk**. Hard request timeouts are **900 s / 1200 s / 2700 s** for `demo / balanced / research`. Timeout handling is SIGTERM → wait 5 s → SIGKILL if required, with no automatic retry.

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

