#!/usr/bin/env python3
"""Blink GPIO outputs and report input states for the Magic Box."""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(BASE_DIR))

import config
from gpiozero import Button, LED


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Magic Box GPIO self-test")
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Monitor input changes for 10 seconds after blinking outputs.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay (seconds) between LED toggles.",
    )
    return parser.parse_args()


def blink_led(led: LED, delay: float) -> None:
    led.on()
    time.sleep(delay)
    led.off()
    time.sleep(delay)


def main() -> int:
    args = parse_args()

    missing = [
        pin.name
        for pin in (
            config.LID_SWITCH,
            config.KEY1_SWITCH,
            config.KEY2_SWITCH,
            config.LID_LED,
            config.KEY1_LED,
            config.KEY2_LED,
            config.MAGIC_LED,
        )
        if pin.bcm_pin is None
    ]
    if missing:
        print("Missing BCM pins for: " + ", ".join(missing))
        return 1

    outputs = {
        "LID_LED": LED(config.LID_LED.bcm_pin, active_high=config.LID_LED.active_high),
        "KEY1_LED": LED(config.KEY1_LED.bcm_pin, active_high=config.KEY1_LED.active_high),
        "KEY2_LED": LED(config.KEY2_LED.bcm_pin, active_high=config.KEY2_LED.active_high),
        "MAGIC_LED": LED(config.MAGIC_LED.bcm_pin, active_high=config.MAGIC_LED.active_high),
    }

    inputs = {
        "LID_SWITCH": Button(
            config.LID_SWITCH.bcm_pin,
            pull_up=config.SWITCH_PULL_UP,
            bounce_time=config.SWITCH_DEBOUNCE_S,
        ),
        "KEY1_SWITCH": Button(
            config.KEY1_SWITCH.bcm_pin,
            pull_up=config.SWITCH_PULL_UP,
            bounce_time=config.SWITCH_DEBOUNCE_S,
        ),
        "KEY2_SWITCH": Button(
            config.KEY2_SWITCH.bcm_pin,
            pull_up=config.SWITCH_PULL_UP,
            bounce_time=config.SWITCH_DEBOUNCE_S,
        ),
    }

    try:
        print("Blinking output LEDs...")
        for name, led in outputs.items():
            print(f"- {name}")
            blink_led(led, args.delay)

        print("\nInput states:")
        for name, button in inputs.items():
            print(f"- {name}: {'PRESSED' if button.is_pressed else 'RELEASED'}")

        if args.monitor:
            print("\nMonitoring input changes for 10 seconds...")
            end_time = time.time() + 10
            last_states = {name: button.is_pressed for name, button in inputs.items()}
            while time.time() < end_time:
                for name, button in inputs.items():
                    state = button.is_pressed
                    if state != last_states[name]:
                        last_states[name] = state
                        print(f"- {name} changed to {'PRESSED' if state else 'RELEASED'}")
                time.sleep(0.05)
    finally:
        for led in outputs.values():
            led.off()
            led.close()
        for button in inputs.values():
            button.close()

    print("Self-test complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
