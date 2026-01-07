"""LED controllers."""

from dataclasses import dataclass
import random
import threading
import time
from typing import Dict, List

from magicbox import config


@dataclass(frozen=True)
class StatusPattern:
    steps: List[tuple[bool, float]]


class StatusCode:
    BOOTING = "booting"
    READY = "ready"
    SERVICE_FAILED = "service_failed"
    WIFI_MISSING = "wifi_missing"
    WEB_DOWN = "web_down"
    GPIO_ERROR = "gpio_error"
    LOG_EXPORT_FAILURE = "log_export_failure"
    UNKNOWN_EXCEPTION = "unknown_exception"


STATUS_PATTERNS: Dict[str, StatusPattern] = {
    StatusCode.BOOTING: StatusPattern(
        [(True, config.BOOT_ON_SECONDS), (False, config.BOOT_OFF_SECONDS)]
    ),
    StatusCode.READY: StatusPattern([(True, 1.0)]),
    StatusCode.SERVICE_FAILED: StatusPattern(
        [
            (True, config.SHORT_BLINK_ON_SECONDS),
            (False, config.SHORT_BLINK_OFF_SECONDS),
            (True, config.SHORT_BLINK_ON_SECONDS),
            (False, config.SHORT_BLINK_OFF_SECONDS),
            (False, config.STATUS_PAUSE_SECONDS),
        ]
    ),
    StatusCode.WIFI_MISSING: StatusPattern(
        [
            (True, config.SHORT_BLINK_ON_SECONDS),
            (False, config.SHORT_BLINK_OFF_SECONDS),
            (True, config.SHORT_BLINK_ON_SECONDS),
            (False, config.SHORT_BLINK_OFF_SECONDS),
            (False, config.STATUS_PAUSE_SECONDS),
        ]
    ),
    StatusCode.WEB_DOWN: StatusPattern(
        [
            (True, config.SHORT_BLINK_ON_SECONDS),
            (False, config.SHORT_BLINK_OFF_SECONDS),
            (True, config.SHORT_BLINK_ON_SECONDS),
            (False, config.SHORT_BLINK_OFF_SECONDS),
            (True, config.SHORT_BLINK_ON_SECONDS),
            (False, config.SHORT_BLINK_OFF_SECONDS),
            (True, config.SHORT_BLINK_ON_SECONDS),
            (False, config.SHORT_BLINK_OFF_SECONDS),
            (True, config.SHORT_BLINK_ON_SECONDS),
            (False, config.SHORT_BLINK_OFF_SECONDS),
            (False, config.STATUS_PAUSE_SECONDS),
        ]
    ),
    StatusCode.GPIO_ERROR: StatusPattern(
        [
            (True, config.SHORT_BLINK_ON_SECONDS),
            (False, config.SHORT_BLINK_OFF_SECONDS),
            (True, config.SHORT_BLINK_ON_SECONDS),
            (False, config.SHORT_BLINK_OFF_SECONDS),
            (True, config.SHORT_BLINK_ON_SECONDS),
            (False, config.SHORT_BLINK_OFF_SECONDS),
            (True, config.SHORT_BLINK_ON_SECONDS),
            (False, config.SHORT_BLINK_OFF_SECONDS),
            (True, config.SHORT_BLINK_ON_SECONDS),
            (False, config.SHORT_BLINK_OFF_SECONDS),
            (True, config.SHORT_BLINK_ON_SECONDS),
            (False, config.SHORT_BLINK_OFF_SECONDS),
            (True, config.SHORT_BLINK_ON_SECONDS),
            (False, config.SHORT_BLINK_OFF_SECONDS),
            (False, config.STATUS_PAUSE_SECONDS),
        ]
    ),
    StatusCode.LOG_EXPORT_FAILURE: StatusPattern(
        [
            (True, config.SHORT_BLINK_ON_SECONDS),
            (False, config.SHORT_BLINK_OFF_SECONDS),
            (False, config.STATUS_PAUSE_SECONDS),
        ]
    ),
    StatusCode.UNKNOWN_EXCEPTION: StatusPattern(
        [(True, config.UNKNOWN_ON_SECONDS), (False, config.UNKNOWN_OFF_SECONDS)]
    ),
}


class StatusLedController(threading.Thread):
    def __init__(self, gpio, logger) -> None:
        super().__init__(daemon=True)
        self._gpio = gpio
        self._logger = logger
        self._code = StatusCode.BOOTING
        self._lock = threading.Lock()
        self._stop_event = threading.Event()

    def set_code(self, code: str) -> None:
        with self._lock:
            if self._code != code:
                self._logger.info("Status LED code set to %s", code)
                self._code = code

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        self._logger.info("Status LED controller started")
        while not self._stop_event.is_set():
            with self._lock:
                code = self._code
            pattern = STATUS_PATTERNS[code]
            for on, duration in pattern.steps:
                if self._stop_event.is_set():
                    break
                self._gpio.set_output("status", on)
                time.sleep(duration)


class MagicLedController:
    def __init__(self, gpio, logger) -> None:
        self._gpio = gpio
        self._logger = logger
        self._thread = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._enabled = True

    def set_enabled(self, enabled: bool) -> None:
        with self._lock:
            self._enabled = enabled
            if not enabled:
                self._logger.info("Magic LED disabled by GPIO gate")
                self._stop_event.set()
                self._gpio.set_output("magic", False)

    def trigger(self) -> None:
        with self._lock:
            if not self._enabled:
                self._logger.info("Magic LED trigger ignored; GPIO gate disabled")
                return
            if self._thread and self._thread.is_alive():
                self._stop_event.set()
                self._thread.join(timeout=1.0)
            self._stop_event = threading.Event()
            self._thread = threading.Thread(target=self._run_effect, daemon=True)
            self._thread.start()

    def _run_effect(self) -> None:
        self._logger.info("Magic LED effect started")
        end_time = time.monotonic() + config.MAGIC_EFFECT_DURATION_SECONDS
        while time.monotonic() < end_time and not self._stop_event.is_set():
            with self._lock:
                enabled = self._enabled
            if not enabled:
                self._gpio.set_output("magic", False)
                break
            self._gpio.set_output("magic", True)
            time.sleep(random.uniform(config.MAGIC_PULSE_MIN_SECONDS, config.MAGIC_PULSE_MAX_SECONDS))
            self._gpio.set_output("magic", False)
            time.sleep(random.uniform(config.MAGIC_PULSE_MIN_SECONDS, config.MAGIC_PULSE_MAX_SECONDS))
        self._gpio.set_output("magic", False)
        self._logger.info("Magic LED effect ended")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1.0)
        self._gpio.set_output("magic", False)
