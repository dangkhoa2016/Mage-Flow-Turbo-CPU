from pathlib import Path

import pytest


def test_generic_package_contains_no_kaggle_absolute_paths():
    root = Path("mageflow_native")
    assert root.is_dir()
    text = "\n".join(
        p.read_text(encoding="utf-8", errors="ignore")
        for p in root.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    )
    assert "/kaggle/input" not in text
    assert "/kaggle/working" not in text
