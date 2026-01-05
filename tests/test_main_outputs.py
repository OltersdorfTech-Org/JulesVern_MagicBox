from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(BASE_DIR))

from main import update_outputs


class FakeSwitch:
    def __init__(self, pressed: bool) -> None:
        self.is_pressed = pressed


class FakeLED:
    def __init__(self) -> None:
        self.state = "off"
        self.value = 0

    def on(self) -> None:
        self.state = "on"
        self.value = 1

    def off(self) -> None:
        self.state = "off"
        self.value = 0


class FakeFlicker:
    def __init__(self) -> None:
        self.enabled = False

    def update(self, enabled: bool) -> None:
        self.enabled = enabled


def build_hw(lid_pressed: bool, key1_pressed: bool, key2_pressed: bool):
    return {
        "lid_switch": FakeSwitch(lid_pressed),
        "key1_switch": FakeSwitch(key1_pressed),
        "key2_switch": FakeSwitch(key2_pressed),
        "lid_led": FakeLED(),
        "key1_led": FakeLED(),
        "key2_led": FakeLED(),
        "flicker": FakeFlicker(),
    }


def test_update_outputs_respects_active_low_switch():
    hw = build_hw(lid_pressed=True, key1_pressed=False, key2_pressed=False)
    lid_closed = update_outputs(hw, remote_lid_on=True, magic_enabled=False, safety_enabled=True)
    assert lid_closed is True
    assert hw["lid_led"].state == "on"

    hw = build_hw(lid_pressed=False, key1_pressed=False, key2_pressed=False)
    lid_closed = update_outputs(hw, remote_lid_on=True, magic_enabled=False, safety_enabled=True)
    assert lid_closed is False
    assert hw["lid_led"].state == "off"


def test_update_outputs_disables_outputs_when_safety_off():
    hw = build_hw(lid_pressed=True, key1_pressed=True, key2_pressed=True)
    lid_closed = update_outputs(hw, remote_lid_on=True, magic_enabled=True, safety_enabled=False)
    assert lid_closed is True
    assert hw["lid_led"].state == "off"
    assert hw["key1_led"].state == "off"
    assert hw["key2_led"].state == "off"
    assert hw["flicker"].enabled is False
