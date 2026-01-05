from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(BASE_DIR))

import config


def test_default_pin_mapping_matches_pi_zero_wiring():
    assert config.LID_SWITCH.bcm_pin == 27
    assert config.LID_SWITCH.physical_pin == 13
    assert config.LID_LED.bcm_pin == 4
    assert config.LID_LED.physical_pin == 7


def test_switch_debounce_is_short():
    assert config.SWITCH_DEBOUNCE_S == 0.05
