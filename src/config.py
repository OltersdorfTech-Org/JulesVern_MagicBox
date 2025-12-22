"""
Configuration for the Magic Lid GPIO controller.

Notes from user clarifications:
- All pin references are physical header pins; BCM mappings are provided below.
- Switches are wired from GPIO to GND with no external pull-ups (uses internal
  pull_up=True in software).
- Lid switch confirmed on BCM13 (physical pin 33).
- Key 2 switch/LED must move to their own GPIO pins; defaults below pick free
  GPIOs but can be changed easily.
"""
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Callable

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("MAGICBOX_DATA_DIR", BASE_DIR / "data"))
STATE_DIR = Path(os.environ.get("MAGICBOX_STATE_DIR", DATA_DIR / "state"))
STATE_DIR.mkdir(parents=True, exist_ok=True)
REMOTE_STATE_FILE = STATE_DIR / "lid_remote_state.json"

# GPIO configuration
@dataclass
class SignalPin:
    name: str
    bcm_pin: Optional[int]
    physical_pin: Optional[int]
    needs_confirmation: bool = True
    note: str = ""

# Pin defaults — adjust if your wiring differs
LID_SWITCH = SignalPin(
    name="LID_SWITCH",
    bcm_pin=13,
    physical_pin=33,
    needs_confirmation=False,
    note="Confirmed by user: Lid switch on BCM13 (physical pin 33).",
)

KEY1_SWITCH = SignalPin(
    name="KEY1_SWITCH",
    bcm_pin=23,  # physical pin 16
    physical_pin=16,
    needs_confirmation=True,
    note="Original mapping kept: physical pin 16 → BCM23. Confirm against wiring.",
)

KEY2_SWITCH = SignalPin(
    name="KEY2_SWITCH",
    bcm_pin=5,  # physical pin 29 (moved to its own GPIO)
    physical_pin=29,
    needs_confirmation=True,
    note="Moved to a dedicated GPIO (BCM5 / pin 29). Update if you choose a different free pin.",
)

LID_LED = SignalPin(
    name="LID_LED",
    bcm_pin=4,  # physical pin 7
    physical_pin=7,
    needs_confirmation=True,
    note="Original LED mapping retained: physical pin 7 → BCM4. Confirm against wiring.",
)

KEY1_LED = SignalPin(
    name="KEY1_LED",
    bcm_pin=24,  # physical pin 18
    physical_pin=18,
    needs_confirmation=True,
    note="Original LED mapping retained: physical pin 18 → BCM24. Confirm against wiring.",
)

KEY2_LED = SignalPin(
    name="KEY2_LED",
    bcm_pin=6,  # physical pin 31 (moved to its own GPIO)
    physical_pin=31,
    needs_confirmation=True,
    note="Moved to a dedicated GPIO (BCM6 / pin 31). Update if you choose a different free pin.",
)

MAGIC_LED = SignalPin(
    name="MAGIC_LED",
    bcm_pin=19,  # physical pin 35 (free; avoids overlap with lid switch on BCM13)
    physical_pin=35,
    needs_confirmation=True,
    note="Placed on BCM19 / pin 35 to avoid conflict with lid switch on BCM13. Update if needed.",
)

# Switch settings
SWITCH_PULL_UP = True  # Active-low expected: switches to GND
SWITCH_DEBOUNCE_S = 0.05

# Magic LED flicker settings
MAGIC_FLICKER_MIN_MS = 50
MAGIC_FLICKER_MAX_MS = 300

# Main loop sleep interval for polling remote state changes
MAIN_LOOP_SLEEP_S = 0.25

# Placeholder predicate: update once the truth table for Magic LED is confirmed.
# The callable should accept (lid_closed: bool, remote_lid_on: bool) -> bool
MagicFlickerPredicate = Callable[[bool, bool], bool]

def default_magic_flicker_predicate(lid_closed: bool, remote_lid_on: bool) -> bool:
    """Return whether the Magic LED should flicker.

    This default is intentionally conservative (always False) until the
    required truth table is confirmed with the user.
    """
    return False

MAGIC_FLICKER_RULE: MagicFlickerPredicate = default_magic_flicker_predicate
