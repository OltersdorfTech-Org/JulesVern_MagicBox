"""GPIO status LED controller with selectable blink patterns."""

from __future__ import annotations

import threading
from typing import Iterable, Tuple

from gpiozero import LED

PatternStep = Tuple[bool, float]


class StatusLED:
    """Manage a single GPIO LED with selectable blink patterns."""

    VALID_MODES = {
        "booting",
        "ready",
        "fault_service",
        "fault_web",
        "fault_wifi",
        "fault_internet",
        "fault_disk",
    }

    def __init__(self, pin: int, log=print) -> None:
        self._log = log
        self._led = LED(pin)
        self._mode = "booting"
        self._mode_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._mode_event = threading.Event()

    def set_mode(self, mode: str) -> None:
        if mode not in self.VALID_MODES:
            raise ValueError(f"Unsupported LED mode: {mode}")
        with self._mode_lock:
            if mode != self._mode:
                self._log(f"Status LED mode changed to: {mode}")
                self._mode = mode
                self._mode_event.set()

    def run(self, patterns: dict[str, Iterable[PatternStep]]) -> None:
        """Run the LED loop until stop() is called."""
        try:
            while not self._stop_event.is_set():
                mode = self._get_mode()
                if mode == "ready":
                    self._led.on()
                    self._wait_for_update(0.25)
                    continue

                pattern = patterns.get(mode, patterns["booting"])
                for state, duration in pattern:
                    if self._stop_event.is_set():
                        break
                    self._led.value = 1 if state else 0
                    if self._wait_for_update(duration):
                        break
        finally:
            self._led.off()
            self._led.close()

    def stop(self) -> None:
        self._stop_event.set()
        self._mode_event.set()

    def stopped(self) -> bool:
        return self._stop_event.is_set()

    def _wait_for_update(self, timeout: float) -> bool:
        """Wait for either timeout or mode change. Returns True if mode changed."""
        if self._mode_event.wait(timeout=timeout):
            self._mode_event.clear()
            return True
        return False

    def _get_mode(self) -> str:
        with self._mode_lock:
            return self._mode
