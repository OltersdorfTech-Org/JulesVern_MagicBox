from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(BASE_DIR))

import gpio_status


def test_write_and_read_status(tmp_path):
    status_path = tmp_path / "status.json"
    gpio_status.write_status(
        status_path,
        lid_closed=True,
        remote_lid_on=False,
        magic_flag_on=True,
        safety_enabled=True,
        last_error=None,
    )
    status = gpio_status.read_status(status_path)
    assert status is not None
    assert status.lid_closed is True
    assert status.remote_lid_on is False
    assert status.magic_flag_on is True
    assert status.safety_enabled is True
