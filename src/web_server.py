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
import time
from collections import deque
from pathlib import Path
from typing import Dict, Optional

from flask import Flask, jsonify, redirect, render_template, request, url_for
import config
import logging_utils
from gpio_status import read_status
from main import RemoteStateStore

APP_PORT_DEFAULT = 8080

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates"

app = Flask(__name__, template_folder=str(TEMPLATE_DIR))
state_store = RemoteStateStore(config.REMOTE_STATE_FILE)
logger = logging_utils.get_logger("magicbox.web", config.LOG_FILE_WEB)

LOG_FILE_OPTIONS = {
    "main": config.LOG_FILE_MAIN,
    "web": config.LOG_FILE_WEB,
    "gpio": config.LOG_FILE_GPIO,
}

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


def read_lid_switch_state() -> tuple[Optional[bool], Optional[str]]:
    """Read lid state from the GPIO service snapshot.

    Returns (lid_closed, error_message).
    """

    status = read_status(config.STATUS_FILE)
    if status is None:
        return None, "GPIO service status file not found."
    if status.updated_at_unix:
        age_s = time.time() - status.updated_at_unix
    else:
        age_s = config.STATUS_STALE_SECONDS + 1
    if age_s > config.STATUS_STALE_SECONDS:
        last_error = status.last_error or "Status heartbeat is stale."
        return None, f"GPIO service down: {last_error}"
    if status.last_error:
        return status.lid_closed, f"GPIO service error: {status.last_error}"
    return status.lid_closed, None


def build_status_payload() -> dict:
    """Compose status details for the template."""

    state = state_store.read_all()
    remote_on = state["remote_lid_on"]
    magic_on = state["magic_flag_on"]
    safety_on = state["safety_enabled"]
    lid_closed, lid_error = read_lid_switch_state()
    return {
        "remote_on": remote_on,
        "magic_on": magic_on,
        "safety_on": safety_on,
        "lid_closed": lid_closed,
        "lid_error": lid_error,
        "pins": {
            "lid_switch_pin": config.LID_SWITCH.physical_pin,
            "lid_led_pin": config.LID_LED.physical_pin,
            "magic_flicker_led_pin": config.MAGIC_LED.physical_pin,
            "key1_led_pin": config.KEY1_LED.physical_pin,
            "key2_led_pin": config.KEY2_LED.physical_pin,
            "key1_switch_pin": config.KEY1_SWITCH.physical_pin,
            "key2_switch_pin": config.KEY2_SWITCH.physical_pin,
        },
        "log_files": list(LOG_FILE_OPTIONS.keys()),
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
    commands = [
        ["systemctl", "start", "jv-poweroff.service"],
        ["sudo", "-n", "systemctl", "start", "jv-poweroff.service"],
    ]

    last_error = None
    for command in commands:
        try:
            result = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=3,
            )
        except FileNotFoundError:
            last_error = f"Command not found: {command[0]}"
            continue
        except subprocess.TimeoutExpired:
            last_error = "Shutdown request timed out."
            continue

        if result.returncode == 0:
            return None

        stderr = result.stderr.strip() or result.stdout.strip()
        if stderr:
            last_error = stderr

    return last_error or "Shutdown request failed."


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


def _read_log_tail(path: Path, lines: int) -> str:
    if lines <= 0:
        return ""
    buffer: deque[str] = deque(maxlen=lines)
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            buffer.append(line.rstrip("\n"))
    return "\n".join(buffer)


@app.get("/api/logs")
def api_logs():
    file_key = request.args.get("file", "main").strip().lower()
    if file_key not in LOG_FILE_OPTIONS:
        return jsonify({"error": "unknown log file"}), 400
    try:
        lines = int(request.args.get("lines", "200"))
    except ValueError:
        lines = 200
    lines = max(1, min(lines, 1000))
    log_path = LOG_FILE_OPTIONS[file_key]
    try:
        payload = _read_log_tail(log_path, lines)
        missing = False
    except FileNotFoundError:
        payload = ""
        missing = True
    return jsonify({"file": file_key, "lines": payload, "missing": missing})


@app.post("/lid/on")
def lid_on():
    guard = _safety_redirect("turn the LID LED on")
    if guard:
        return guard
    state_store.write(True)
    logger.info("LID flag set to ON (web)")
    return redirect(url_for("index", notice="LID flag set to ON"))


@app.post("/lid/off")
def lid_off():
    guard = _safety_redirect("turn the LID LED off")
    if guard:
        return guard
    state_store.write(False)
    logger.info("LID flag set to OFF (web)")
    return redirect(url_for("index", notice="LID flag set to OFF"))


@app.post("/lid/toggle")
def lid_toggle():
    guard = _safety_redirect("toggle the LID LED flag")
    if guard:
        return guard
    new_state = state_store.toggle()
    logger.info("LID flag toggled to %s (web)", "ON" if new_state else "OFF")
    return redirect(
        url_for("index", notice=f"LID flag toggled to {'ON' if new_state else 'OFF'}")
    )


@app.post("/magic/toggle")
def magic_toggle():
    guard = _safety_redirect("toggle magic flicker")
    if guard:
        return guard
    new_state = state_store.toggle_magic()
    logger.info("Magic flicker flag toggled to %s (web)", "ON" if new_state else "OFF")
    return redirect(
        url_for("index", notice=f"Magic flag toggled to {'ON' if new_state else 'OFF'}")
    )


@app.post("/safety/toggle")
def safety_toggle():
    new_state = state_store.toggle_safety()
    logger.info("Safety toggled to %s (web)", "ENABLED" if new_state else "DISABLED")
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

    logger.info("GPIO pins updated via web UI.")
    return redirect(url_for("index", notice="GPIO pins updated in config.py"))


@app.post("/shutdown")
def shutdown():
    error = request_shutdown()
    if error:
        return redirect(url_for("index", alert=f"Shutdown failed: {error}"))
    logger.info("Shutdown requested via web UI.")
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
    logger.info(
        "Starting Magic Lid web UI on http://0.0.0.0:%s — intended for trusted home networks.",
        args.port,
    )
    logging_utils.log_startup_banner(logger, "web")
    app.run(host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()
