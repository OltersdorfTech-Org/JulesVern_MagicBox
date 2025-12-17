"""Magic Lid GPIO controller for Raspberry Pi.

This script can run as a background service to manage LEDs and switches,
or be called with CLI flags to adjust the remote LID LED state.
"""
import argparse
import json
import os
import random
import signal
import tempfile
import time
from pathlib import Path
from threading import Event, Thread
from typing import Optional

from gpiozero import Button, LED

import config


class RemoteStateStore:
    """Persist and load toggleable flags for the controller."""

    DEFAULT_STATE = {
        "remote_lid_on": True,
        "magic_flag_on": False,
        "safety_enabled": False,
    }

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _write_state(self, state: dict) -> None:
        merged = {**self.DEFAULT_STATE, **state}
        with tempfile.NamedTemporaryFile(
            "w", dir=self.path.parent, encoding="utf-8", delete=False
        ) as handle:
            json.dump(merged, handle)
            handle.flush()
            os.fsync(handle.fileno())
            tmp_name = handle.name
        Path(tmp_name).replace(self.path)

    def read_all(self) -> dict:
        if not self.path.exists():
            return dict(self.DEFAULT_STATE)
        with self.path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return {
            "remote_lid_on": bool(data.get("remote_lid_on", True)),
            "magic_flag_on": bool(data.get("magic_flag_on", False)),
            "safety_enabled": bool(data.get("safety_enabled", False)),
        }

    def read(self) -> bool:
        return self.read_all()["remote_lid_on"]

    def read_magic(self) -> bool:
        return self.read_all()["magic_flag_on"]

    def read_safety(self) -> bool:
        return self.read_all()["safety_enabled"]

    def write(self, enabled: bool) -> None:
        state = self.read_all()
        state["remote_lid_on"] = bool(enabled)
        self._write_state(state)

    def write_magic(self, enabled: bool) -> None:
        state = self.read_all()
        state["magic_flag_on"] = bool(enabled)
        self._write_state(state)

    def write_safety(self, enabled: bool) -> None:
        state = self.read_all()
        state["safety_enabled"] = bool(enabled)
        self._write_state(state)

    def toggle(self) -> bool:
        new_state = not self.read()
        self.write(new_state)
        return new_state

    def toggle_magic(self) -> bool:
        new_state = not self.read_magic()
        self.write_magic(new_state)
        return new_state

    def toggle_safety(self) -> bool:
        new_state = not self.read_safety()
        self.write_safety(new_state)
        return new_state


class MagicFlickerWorker:
    """Background flicker controller for the Magic LED."""

    def __init__(self, led: LED, stop_event: Event) -> None:
        self.led = led
        self.stop_event = stop_event
        self.enabled = False
        self.thread = Thread(target=self._run, daemon=True)

    def start(self) -> None:
        if not self.thread.is_alive():
            self.thread.start()

    def join(self, timeout: Optional[float] = None) -> None:
        if self.thread.is_alive():
            self.thread.join(timeout)

    def update(self, enabled: bool) -> None:
        self.enabled = enabled
        if not enabled:
            self.led.off()

    def _run(self) -> None:
        while not self.stop_event.is_set():
            if self.enabled:
                self.led.toggle()
                delay_ms = random.randint(
                    config.MAGIC_FLICKER_MIN_MS, config.MAGIC_FLICKER_MAX_MS
                )
                time.sleep(delay_ms / 1000)
            else:
                self.led.off()
                time.sleep(0.1)
        self.led.off()


def require_pins(*pins: config.SignalPin) -> None:
    missing = [p.name for p in pins if p.bcm_pin is None]
    if missing:
        message = (
            "GPIO pin numbers are missing for: " + ", ".join(missing) +
            "\nUpdate src/config.py with BCM pin numbers before running."
        )
        raise SystemExit(message)


def build_hardware(stop_event: Event):
    require_pins(
        config.LID_SWITCH,
        config.KEY1_SWITCH,
        config.KEY2_SWITCH,
        config.LID_LED,
        config.KEY1_LED,
        config.KEY2_LED,
        config.MAGIC_LED,
    )

    lid_switch = Button(
        config.LID_SWITCH.bcm_pin,
        pull_up=config.SWITCH_PULL_UP,
        bounce_time=config.SWITCH_DEBOUNCE_S,
    )
    key1_switch = Button(
        config.KEY1_SWITCH.bcm_pin,
        pull_up=config.SWITCH_PULL_UP,
        bounce_time=config.SWITCH_DEBOUNCE_S,
    )
    key2_switch = Button(
        config.KEY2_SWITCH.bcm_pin,
        pull_up=config.SWITCH_PULL_UP,
        bounce_time=config.SWITCH_DEBOUNCE_S,
    )

    lid_led = LED(config.LID_LED.bcm_pin)
    key1_led = LED(config.KEY1_LED.bcm_pin)
    key2_led = LED(config.KEY2_LED.bcm_pin)
    magic_led = LED(config.MAGIC_LED.bcm_pin)

    flicker_worker = MagicFlickerWorker(magic_led, stop_event)
    flicker_worker.start()

    return {
        "lid_switch": lid_switch,
        "key1_switch": key1_switch,
        "key2_switch": key2_switch,
        "lid_led": lid_led,
        "key1_led": key1_led,
        "key2_led": key2_led,
        "magic_led": magic_led,
        "flicker": flicker_worker,
    }


def update_outputs(hw, remote_lid_on: bool, magic_enabled: bool, safety_enabled: bool) -> None:
    if not safety_enabled:
        hw["lid_led"].off()
        hw["key1_led"].off()
        hw["key2_led"].off()
        hw["flicker"].update(False)
        return

    lid_closed = hw["lid_switch"].is_pressed  # active-low switch to GND
    key1_closed = hw["key1_switch"].is_pressed
    key2_closed = hw["key2_switch"].is_pressed

    # LID LED obeys both lid switch and remote state
    if lid_closed and remote_lid_on:
        hw["lid_led"].on()
    else:
        hw["lid_led"].off()

    # Key LEDs mirror their switches
    hw["key1_led"].value = 1 if key1_closed else 0
    hw["key2_led"].value = 1 if key2_closed else 0

    # Magic LED flicker control
    should_flicker = magic_enabled and config.MAGIC_FLICKER_RULE(lid_closed, remote_lid_on)
    hw["flicker"].update(should_flicker)


class ServiceRunner:
    def __init__(self) -> None:
        self.stop_event = Event()
        self.remote_store = RemoteStateStore(config.REMOTE_STATE_FILE)
        self.hardware = build_hardware(self.stop_event)
        state = self.remote_store.read_all()
        self.remote_lid_on = state["remote_lid_on"]
        self.magic_enabled = state["magic_flag_on"]
        self.safety_enabled = state["safety_enabled"]

    def start(self) -> None:
        print("Magic Lid service starting...")
        self._setup_signal_handlers()
        self._attach_switch_handlers()
        print(
            "Startup state — "
            f"Safety: {'ENABLED' if self.safety_enabled else 'DISABLED'}, "
            f"Remote LID: {'ON' if self.remote_lid_on else 'OFF'}, "
            f"Magic: {'ON' if self.magic_enabled else 'OFF'}"
        )
        update_outputs(
            self.hardware, self.remote_lid_on, self.magic_enabled, self.safety_enabled
        )
        self._run_loop()

    def _setup_signal_handlers(self) -> None:
        signal.signal(signal.SIGINT, self._stop)
        signal.signal(signal.SIGTERM, self._stop)

    def _attach_switch_handlers(self) -> None:
        lid_switch: Button = self.hardware["lid_switch"]
        key1_switch: Button = self.hardware["key1_switch"]
        key2_switch: Button = self.hardware["key2_switch"]

        lid_switch.when_pressed = lambda: self._handle_state_change("LID switch pressed")
        lid_switch.when_released = lambda: self._handle_state_change("LID switch released")
        key1_switch.when_pressed = lambda: self._handle_state_change("Key1 pressed")
        key1_switch.when_released = lambda: self._handle_state_change("Key1 released")
        key2_switch.when_pressed = lambda: self._handle_state_change("Key2 pressed")
        key2_switch.when_released = lambda: self._handle_state_change("Key2 released")

    def _handle_state_change(self, message: str) -> None:
        print(message)
        update_outputs(
            self.hardware, self.remote_lid_on, self.magic_enabled, self.safety_enabled
        )

    def _run_loop(self) -> None:
        while not self.stop_event.is_set():
            new_state = self.remote_store.read_all()
            if new_state != {
                "remote_lid_on": self.remote_lid_on,
                "magic_flag_on": self.magic_enabled,
                "safety_enabled": self.safety_enabled,
            }:
                if new_state["remote_lid_on"] != self.remote_lid_on:
                    self.remote_lid_on = new_state["remote_lid_on"]
                    print(
                        "Remote LID state updated to: "
                        f"{'ON' if self.remote_lid_on else 'OFF'}"
                    )
                if new_state["magic_flag_on"] != self.magic_enabled:
                    self.magic_enabled = new_state["magic_flag_on"]
                    print(
                        "Magic flicker flag updated to: "
                        f"{'ON' if self.magic_enabled else 'OFF'}"
                    )
                if new_state["safety_enabled"] != self.safety_enabled:
                    self.safety_enabled = new_state["safety_enabled"]
                    print(
                        "Safety state updated to: "
                        f"{'ENABLED' if self.safety_enabled else 'DISABLED'}"
                    )
                update_outputs(
                    self.hardware,
                    self.remote_lid_on,
                    self.magic_enabled,
                    self.safety_enabled,
                )
            time.sleep(config.MAIN_LOOP_SLEEP_S)
        self._cleanup()

    def _stop(self, *_args) -> None:
        print("Received stop signal; cleaning up...")
        self.stop_event.set()

    def _cleanup(self) -> None:
        self.stop_event.set()
        flicker: MagicFlickerWorker = self.hardware["flicker"]
        flicker.update(False)
        flicker.join(timeout=1.0)
        self.hardware["lid_led"].off()
        self.hardware["key1_led"].off()
        self.hardware["key2_led"].off()
        self.hardware["magic_led"].off()
        for device in self.hardware.values():
            if hasattr(device, "close"):
                device.close()
        print("GPIO cleaned up. Exiting.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Magic Lid GPIO controller")
    parser.add_argument(
        "--set-lid-remote",
        choices=["on", "off", "toggle"],
        help="Set or toggle the remote LID LED enable flag and exit.",
    )
    parser.add_argument(
        "--print-status",
        action="store_true",
        help="Print the current remote LID state and exit.",
    )
    return parser.parse_args()


def handle_cli(args: argparse.Namespace, store: RemoteStateStore) -> Optional[bool]:
    if args.set_lid_remote:
        if args.set_lid_remote == "on":
            store.write(True)
            print("Remote LID LED state set to ON")
        elif args.set_lid_remote == "off":
            store.write(False)
            print("Remote LID LED state set to OFF")
        elif args.set_lid_remote == "toggle":
            new_state = store.toggle()
            print(f"Remote LID LED toggled to {'ON' if new_state else 'OFF'}")
        return True

    if args.print_status:
        state = store.read_all()
        print(
            "Current state: "
            f"Remote LID {'ON' if state['remote_lid_on'] else 'OFF'}, "
            f"Magic {'ON' if state['magic_flag_on'] else 'OFF'}, "
            f"Safety {'ENABLED' if state['safety_enabled'] else 'DISABLED'}"
        )
        return True

    return None


def main() -> None:
    args = parse_args()
    store = RemoteStateStore(config.REMOTE_STATE_FILE)
    cli_only = handle_cli(args, store)
    if cli_only:
        return
    runner = ServiceRunner()
    runner.start()


if __name__ == "__main__":
    main()
