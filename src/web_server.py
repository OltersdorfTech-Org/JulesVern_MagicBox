"""Lightweight Flask web server for controlling the remote LID LED flag.

The web interface mirrors the existing CLI options, providing large buttons
that toggle the persisted remote LID state while the background GPIO service
keeps hardware in sync. Status text is kept simple and is intended for use on
trusted home networks.
"""
import argparse
from pathlib import Path
from typing import Optional

from flask import Flask, redirect, render_template, url_for
from gpiozero import Button

import config
from main import RemoteStateStore

APP_PORT_DEFAULT = 8080

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates"

app = Flask(__name__, template_folder=str(TEMPLATE_DIR))
state_store = RemoteStateStore(config.REMOTE_STATE_FILE)


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

    remote_on = state_store.read()
    lid_closed = read_lid_switch_state()
    return {
        "remote_on": remote_on,
        "lid_closed": lid_closed,
    }


@app.route("/")
def index():
    status = build_status_payload()
    return render_template("remote_control.html", **status)


@app.post("/lid/on")
def lid_on():
    state_store.write(True)
    return redirect(url_for("index"))


@app.post("/lid/off")
def lid_off():
    state_store.write(False)
    return redirect(url_for("index"))


@app.post("/lid/toggle")
def lid_toggle():
    state_store.toggle()
    return redirect(url_for("index"))


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
