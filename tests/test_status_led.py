from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1] / "src" / "hardware"
sys.path.insert(0, str(BASE_DIR))

import status_led_daemon as daemon


def test_decide_mode_prioritizes_service_failure():
    mode = daemon.decide_mode(
        main_state="failed",
        web_state="active",
        wifi_ok=True,
        internet_ok=True,
        disk_ok=True,
    )
    assert mode == "fault_service"


def test_decide_mode_reports_web_failure_when_main_ok():
    mode = daemon.decide_mode(
        main_state="active",
        web_state="inactive",
        wifi_ok=True,
        internet_ok=True,
        disk_ok=True,
    )
    assert mode == "fault_web"


def test_decide_mode_reports_disk_before_network():
    mode = daemon.decide_mode(
        main_state="active",
        web_state="active",
        wifi_ok=False,
        internet_ok=False,
        disk_ok=False,
    )
    assert mode == "fault_disk"
