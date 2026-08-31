import json
from pathlib import Path

from mageflow_native.config import default_model_root, default_runtime_root


def test_default_runtime_root_respects_env(monkeypatch, tmp_path):
    root = tmp_path / "rt"
    monkeypatch.setenv("MAGE_RUNTIME_ROOT", str(root))
    assert default_runtime_root() == root


def test_default_runtime_root_xdg(monkeypatch, tmp_path):
    monkeypatch.delenv("MAGE_RUNTIME_ROOT", raising=False)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    assert default_runtime_root().name == "mage-flow-turbo-native"


def test_default_runtime_root_no_kaggle(monkeypatch):
    monkeypatch.delenv("MAGE_RUNTIME_ROOT", raising=False)
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    root = default_runtime_root()
    assert "/kaggle" not in str(root)


def test_default_model_root_env(monkeypatch, tmp_path):
    mr = tmp_path / "models"
    monkeypatch.setenv("MAGE_MODEL_ROOT", str(mr))
    assert default_model_root() == mr


def test_default_model_root_none_by_default(monkeypatch):
    monkeypatch.delenv("MAGE_MODEL_ROOT", raising=False)
    assert default_model_root() is None


def test_doctor_output_is_secret_safe(tmp_path):
    from mageflow_native.cli import build_parser, cmd_doctor

    parser = build_parser()
    args = parser.parse_args(
        ["doctor", "--manifest", str(tmp_path / "manifest.json"), "--json"]
    )
    import io
    import sys
    captured = io.StringIO()
    old = sys.stdout
    sys.stdout = captured
    try:
        code = cmd_doctor(args)
    finally:
        sys.stdout = old
    assert code == 0
    data = json.loads(captured.getvalue())
    assert "product" in data
    assert data["manifest_loaded"] is False  # manifest file doesn't exist
    assert "token" not in captured.getvalue().lower()
    assert "authorization" not in captured.getvalue().lower()
