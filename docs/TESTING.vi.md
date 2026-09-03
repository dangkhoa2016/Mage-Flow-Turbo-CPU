# Kiểm thử (Testing)

Mage-Flow-Turbo-Native-Inference được kiểm thử qua unit/contract tests (không cần trọng số mô hình thật), kiểm tra publication tĩnh và các cổng qualification thật.

## Bộ kiểm thử tĩnh (không có trọng số mô hình)

```bash
python -m pip install -e .
python -m pytest tests/ -q
```

Các contract được bảo phủ:

- xác thực manifest và SHA (`tests/unit/test_manifest.py`)
- xác thực backend/placement (`tests/unit/test_runtime_spec.py`)
- runtime manager và identity (`tests/unit/test_runtime_manager.py`)
- argv inference và runner (`tests/unit/test_inference_*.py`)
- REST API (`tests/contracts/test_rest_api.py`)
- CLI và kết quả `doctor` không lộ bí mật (`tests/contracts/test_cli_contract.py`, `tests/unit/test_cli_doctor.py`)
- không phụ thuộc Kaggle trong core (`tests/contracts/test_no_kaggle_core_dependency.py`)
- notebook contract (`tests/contracts/test_notebook_contract.py`)
- qualification harnesses (`tests/contracts/test_qualification_contract.py`)
- publication surface (`tests/contracts/test_publication_surface.py`)
- adapter Kaggle (`tests/integration/test_kaggle_adapter.py`)

## Cổng tĩnh

```bash
python -m compileall -q mageflow_native integrations scripts
python scripts/publication/audit_public_surface.py --root .
for f in $(find scripts -type f -name '*.sh'); do bash -n "$f"; done
python -m json.tool notebooks/kaggle-production-demo.ipynb >/dev/null
```

## Acceptance CPU chuẩn

Yêu cầu ba file mô hình, một `sd-cli` CPU đã build/xác minh và máy Linux CPU. Đúng một lần sinh chuẩn: 512×512, seed 42, 4 bước, CFG 1.0, 4 threads, prompt cáo chuẩn.

## Acceptance NVIDIA CUDA

Cùng request, backend tường minh `cuda0`, không fallback CPU âm thầm, PNG RGB 512×512 hợp lệ, hash mô hình, bằng chứng device CUDA, telemetry RAM/VRAM và ghi lại PNG SHA tham chiếu CUDA (có thể khác byte so với CPU).

## Proof layout cục bộ

`bash scripts/qualification/run-local-layout-proof.sh --dit ... --qwen ... --vae ...` chạy `doctor` + `verify` chung trong `/tmp/mageflow-native-portability-proof` với runtime root không phải Kaggle, chứng minh core không phụ thuộc filesystem Kaggle.

## Đóng gói evidence

`python scripts/qualification/package-evidence.py ...` tạo `tar.gz` đã khử nhạy cảm kèm sidecar và `MANIFEST.sha256`, fail khi có mẫu bí mật.
