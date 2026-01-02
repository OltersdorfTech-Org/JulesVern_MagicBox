import tempfile
from pathlib import Path

import sys

BASE_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(BASE_DIR))

from log_export import select_boot_root


def test_select_boot_root_prefers_existing():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        candidate1 = temp_path / "boot"
        candidate2 = temp_path / "boot2"
        candidate2.mkdir()
        selected = select_boot_root([candidate1, candidate2])
        assert selected == candidate2


def test_select_boot_root_raises_when_missing():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        candidate1 = temp_path / "boot"
        try:
            select_boot_root([candidate1])
        except FileNotFoundError as exc:
            assert "No boot partition" in str(exc)
        else:
            raise AssertionError("Expected FileNotFoundError")
