"""Thread-safe state store."""

from dataclasses import dataclass
import threading


@dataclass(frozen=True)
class SystemSnapshot:
    message_received: bool
    gpio_enabled: bool
    lid_open: bool
    key1_pressed: bool
    key2_pressed: bool


class StateStore:
    def __init__(self, message_received: bool, gpio_enabled: bool) -> None:
        self._message_received = message_received
        self._gpio_enabled = gpio_enabled
        self._lid_open = False
        self._key1_pressed = False
        self._key2_pressed = False
        self._lock = threading.Lock()

    def snapshot(self) -> SystemSnapshot:
        with self._lock:
            return self._snapshot_locked()

    def _snapshot_locked(self) -> SystemSnapshot:
        return SystemSnapshot(
            message_received=self._message_received,
            gpio_enabled=self._gpio_enabled,
            lid_open=self._lid_open,
            key1_pressed=self._key1_pressed,
            key2_pressed=self._key2_pressed,
        )

    def update_inputs(self, lid_open: bool, key1_pressed: bool, key2_pressed: bool) -> SystemSnapshot:
        with self._lock:
            self._lid_open = lid_open
            self._key1_pressed = key1_pressed
            self._key2_pressed = key2_pressed
            return self._snapshot_locked()

    def set_message_received(self, value: bool) -> SystemSnapshot:
        with self._lock:
            self._message_received = value
            return self._snapshot_locked()

    def set_gpio_enabled(self, value: bool) -> SystemSnapshot:
        with self._lock:
            self._gpio_enabled = value
            return self._snapshot_locked()

    def set_web_state(self, message_received: bool, gpio_enabled: bool) -> SystemSnapshot:
        with self._lock:
            self._message_received = message_received
            self._gpio_enabled = gpio_enabled
            return self._snapshot_locked()
