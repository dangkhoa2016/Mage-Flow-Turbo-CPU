import pytest

from mageflow_native.runtime.spec import BackendSpec, RuntimeBuildBackend


@pytest.mark.parametrize(
    "backend",
    [
        "auto",
        "cpu",
        "cuda0",
    ],
)
def test_simple_backend_valid(backend):
    spec = BackendSpec(backend=backend)
    assert spec.backend == backend


def test_invalid_simple_backend():
    with pytest.raises(ValueError):
        BackendSpec(backend="gpu0;rm -rf /")


def test_advanced_assignment_valid():
    spec = BackendSpec(
        backend="diffusion=cuda0,te=cpu,vae=cpu",
        params_backend="diffusion=cuda0,te=cpu,vae=cpu",
        max_vram="4G",
        split_mode="layers",
    )
    assert spec.backend.startswith("diffusion=")


def test_advanced_assignment_rejects_metacharacters():
    with pytest.raises(ValueError):
        BackendSpec(backend="cuda0;touch /tmp/pwn")


def test_advanced_assignment_rejects_newline():
    with pytest.raises(ValueError):
        BackendSpec(backend="cuda0\ncpu")


def test_auto_fit_rejects_explicit_assignments():
    with pytest.raises(ValueError):
        BackendSpec(backend="cuda0", auto_fit=True)


def test_auto_fit_valid_alone():
    spec = BackendSpec(backend="auto", auto_fit=True)
    assert spec.auto_fit is True


def test_build_backend_flags_cpu():
    flags = RuntimeBuildBackend("cpu").cmake_flags
    assert "-DSD_CUDA=OFF" in flags
    assert "-DSD_CUDA=ON" not in flags
    assert "-DGGML_CUDA_NO_VMM=ON" not in flags
    assert "-DSD_METAL=OFF" in flags
    assert "-DGGML_NATIVE=ON" in flags


def test_build_backend_flags_cuda():
    flags = RuntimeBuildBackend("cuda").cmake_flags
    assert "-DSD_CUDA=ON" in flags
    assert "-DGGML_CUDA_NO_VMM=ON" in flags
    assert "-DGGML_NATIVE=ON" in flags


def test_build_backend_invalid():
    with pytest.raises(ValueError):
        RuntimeBuildBackend("metal")
