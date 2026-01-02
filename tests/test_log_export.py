import tempfile
from pathlib import Path

import sys

BASE_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(BASE_DIR))

import log_export


def test_select_boot_root_prefers_existing():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        candidate1 = temp_path / "boot"
        candidate2 = temp_path / "boot2"
        candidate2.mkdir()
        selected = log_export.select_boot_root([candidate1, candidate2])
        assert selected == candidate2


def test_select_boot_root_raises_when_missing():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        candidate1 = temp_path / "boot"
        try:
            log_export.select_boot_root([candidate1])
        except FileNotFoundError as exc:
            assert "No boot partition" in str(exc)
        else:
            raise AssertionError("Expected FileNotFoundError")


def test_build_export_bundle_uses_timestamped_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(log_export, "_run_command", lambda _cmd: "ok")
    state_file = tmp_path / "state.json"
    state_file.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(log_export.config, "REMOTE_STATE_FILE", state_file)
    export_dir = log_export.build_export_bundle(tmp_path)
    assert export_dir.exists()
    assert (export_dir / "system_info.txt").exists()
    assert (export_dir / "config_snapshot.json").exists()
    assert (export_dir / "state_snapshot.json").exists()
