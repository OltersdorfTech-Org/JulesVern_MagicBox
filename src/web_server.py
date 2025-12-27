"""Lightweight Flask web server for controlling remote flags and safety.

The web interface mirrors the existing CLI options, providing large buttons
that toggle the persisted remote LID state while the background GPIO service
keeps hardware in sync. It also exposes Magic flicker and Safety toggles plus
a GPIO pin editor. Status text is kept simple and is intended for use on
trusted home networks.
"""
import argparse
import importlib
import re
import subprocess
from pathlib import Path
from typing import Dict, Optional

from flask import Flask, redirect, render_template, request, url_for
from gpiozero import Button

import config
from main import RemoteStateStore

APP_PORT_DEFAULT = 8080

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates"

app = Flask(__name__, template_folder=str(TEMPLATE_DIR))
state_store = RemoteStateStore(config.REMOTE_STATE_FILE)

PHYSICAL_TO_BCM: Dict[int, Optional[int]] = {
    1: None,
    2: None,
    3: 2,
    4: None,
    5: 3,
    6: None,
    7: 4,
    8: 14,
    9: None,
    10: 15,
    11: 17,
    12: 18,
    13: 27,
    14: None,
    15: 22,
    16: 23,
    17: None,
    18: 24,
    19: 10,
    20: None,
    21: 9,
    22: 25,
    23: 11,
    24: 8,
    25: None,
    26: 7,
    27: 0,
    28: 1,
    29: 5,
    30: None,
    31: 6,
    32: 12,
    33: 13,
    34: None,
    35: 19,
    36: 16,
    37: 26,
    38: 20,
    39: None,
    40: 21,
}

PIN_FIELD_MAP = {
    "lid_switch_pin": "LID_SWITCH",
    "lid_led_pin": "LID_LED",
    "magic_flicker_led_pin": "MAGIC_LED",
    "key1_led_pin": "KEY1_LED",
    "key2_led_pin": "KEY2_LED",
    "key1_switch_pin": "KEY1_SWITCH",
    "key2_switch_pin": "KEY2_SWITCH",
}

PIN_DIAGRAM = """
Raspberry Pi 40-pin header (physical numbers)

 3V3  (1) (2)  5V
 GPIO2 (3) (4)  5V
 GPIO3 (5) (6) GND
 GPIO4 (7) (8) GPIO14
  GND  (9) (10) GPIO15
 GPIO17(11) (12) GPIO18
 GPIO27(13) (14) GND
 GPIO22(15) (16) GPIO23
 3V3  (17) (18) GPIO24
 GPIO10(19) (20) GND
 GPIO9 (21) (22) GPIO25
 GPIO11(23) (24) GPIO8
  GND  (25) (26) GPIO7
 GPIO0 (27) (28) GPIO1
 GPIO5 (29) (30) GND
 GPIO6 (31) (32) GPIO12
 GPIO13(33) (34) GND
 GPIO19(35) (36) GPIO16
 GPIO26(37) (38) GPIO20
  GND  (39) (40) GPIO21
"""


def read_lid_switch_state() -> Optional[bool]:
    """Read the lid switch state if available.

    Returns True when the lid is closed (switch pressed), False when open, and
    None if the state cannot be determined (e.g., missing hardware).
    """

    try:
        lid_button = Button(
            config.LID_SWITCH.bcm_pin,
            pull_up=config.SWITCH_PULL_UP,
            bounce_time=config.SWITCH_DEBOUNCE_S,
        )
        is_pressed = lid_button.is_pressed
        lid_button.close()
        return is_pressed
    except Exception as exc:  # noqa: BLE001 - broad catch keeps UI alive on hardware errors
        print(f"Warning: unable to read lid switch state ({exc})")
        return None


def build_status_payload() -> dict:
    """Compose status details for the template."""

    state = state_store.read_all()
    remote_on = state["remote_lid_on"]
    magic_on = state["magic_flag_on"]
    safety_on = state["safety_enabled"]
    lid_closed = read_lid_switch_state()
    return {
        "remote_on": remote_on,
        "magic_on": magic_on,
        "safety_on": safety_on,
        "lid_closed": lid_closed,
        "pins": {
            "lid_switch_pin": config.LID_SWITCH.physical_pin,
            "lid_led_pin": config.LID_LED.physical_pin,
            "magic_flicker_led_pin": config.MAGIC_LED.physical_pin,
            "key1_led_pin": config.KEY1_LED.physical_pin,
            "key2_led_pin": config.KEY2_LED.physical_pin,
            "key1_switch_pin": config.KEY1_SWITCH.physical_pin,
            "key2_switch_pin": config.KEY2_SWITCH.physical_pin,
        },
    }


def _safety_redirect(action: str):
    if not state_store.read_safety():
        return redirect(
            url_for(
                "index",
                alert=f"Safety is disabled; cannot {action}. Enable safety to use controls.",
            )
        )
    return None


def update_config_file(pin_updates: Dict[str, int]) -> None:
    config_path = Path(config.__file__).resolve()
    content = config_path.read_text(encoding="utf-8")

    for field, physical_pin in pin_updates.items():
        bcm_pin = PHYSICAL_TO_BCM.get(physical_pin)
        block = PIN_FIELD_MAP[field]
        pattern = re.compile(
            rf"({block}\s*=\s*SignalPin\(\s*name=\"{block}\",\s*bcm_pin=)([^,]+)(,.*?physical_pin=)([^,]+)(,)",
            re.DOTALL,
        )

        def _replace(match: re.Match[str]) -> str:
            return (
                f"{match.group(1)}{bcm_pin}{match.group(3)}{physical_pin}{match.group(5)}"
            )

        content, replaced = pattern.subn(_replace, content, count=1)
        if replaced == 0:
            raise ValueError(f"Could not update pin block for {block}")

    config_path.write_text(content, encoding="utf-8")
    importlib.reload(config)


def request_shutdown() -> Optional[str]:
    """Request a safe system shutdown via systemd."""
    try:
        result = subprocess.run(
            ["systemctl", "start", "jv-poweroff.service"],
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except FileNotFoundError:
        return "systemctl not found on this system."
    except subprocess.TimeoutExpired:
        return "Shutdown request timed out."

    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        return stderr or "Shutdown request failed."
    return None


@app.route("/")
def index():
    status = build_status_payload()
    alert = request.args.get("alert")
    notice = request.args.get("notice")
    return render_template(
        "remote_control.html",
        pin_diagram=PIN_DIAGRAM,
        alert=alert,
        notice=notice,
        **status,
    )


@app.post("/lid/on")
def lid_on():
    guard = _safety_redirect("turn the LID LED on")
    if guard:
        return guard
    state_store.write(True)
    return redirect(url_for("index", notice="LID flag set to ON"))


@app.post("/lid/off")
def lid_off():
    guard = _safety_redirect("turn the LID LED off")
    if guard:
        return guard
    state_store.write(False)
    return redirect(url_for("index", notice="LID flag set to OFF"))


@app.post("/lid/toggle")
def lid_toggle():
    guard = _safety_redirect("toggle the LID LED flag")
    if guard:
        return guard
    new_state = state_store.toggle()
    return redirect(
        url_for("index", notice=f"LID flag toggled to {'ON' if new_state else 'OFF'}")
    )


@app.post("/magic/toggle")
def magic_toggle():
    guard = _safety_redirect("toggle magic flicker")
    if guard:
        return guard
    new_state = state_store.toggle_magic()
    return redirect(
        url_for("index", notice=f"Magic flag toggled to {'ON' if new_state else 'OFF'}")
    )


@app.post("/safety/toggle")
def safety_toggle():
    new_state = state_store.toggle_safety()
    if not new_state:
        notice = "Safety disabled: outputs will remain off and controls are locked."
    else:
        notice = "Safety enabled: controls are now active."
    return redirect(url_for("index", notice=notice))


@app.post("/pins/update")
def pins_update():
    errors = []
    updates: Dict[str, int] = {}
    for field in PIN_FIELD_MAP:
        raw_value = request.form.get(field, "").strip()
        if not raw_value:
            errors.append(f"{field.replace('_', ' ').title()} is required")
            continue
        if not raw_value.isdigit():
            errors.append(f"{raw_value} is not a valid integer for {field}")
            continue
        physical_pin = int(raw_value)
        bcm_pin = PHYSICAL_TO_BCM.get(physical_pin)
        if bcm_pin is None:
            errors.append(
                f"Physical pin {physical_pin} is not a usable GPIO. Use a numbered GPIO pin."
            )
            continue
        updates[field] = physical_pin

    if errors:
        return redirect(url_for("index", alert="; ".join(errors)))

    try:
        update_config_file(updates)
    except Exception as exc:  # noqa: BLE001
        return redirect(url_for("index", alert=f"Failed to update config: {exc}"))

    return redirect(url_for("index", notice="GPIO pins updated in config.py"))


@app.post("/shutdown")
def shutdown():
    error = request_shutdown()
    if error:
        return redirect(url_for("index", alert=f"Shutdown failed: {error}"))
    return redirect(url_for("index", notice="Shutdown requested. System will power off shortly."))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Magic Lid web controller")
    parser.add_argument(
        "--port",
        type=int,
        default=APP_PORT_DEFAULT,
        help="TCP port to bind the web server (default: 8080)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(
        f"Starting Magic Lid web UI on http://0.0.0.0:{args.port} — intended for trusted home networks."
    )
    app.run(host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()
