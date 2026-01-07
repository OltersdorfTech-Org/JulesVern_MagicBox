"""Health monitoring and status aggregation."""

import http.client
import os
import shutil
import subprocess
import threading
import time

from magicbox import config
from magicbox.leds import StatusCode


class StatusManager:
    def __init__(self, status_led, logger) -> None:
        self._status_led = status_led
        self._logger = logger
        self._lock = threading.Lock()
        self._flags = {
            "gpio_error": False,
            "web_down": False,
            "log_export_failure": False,
            "wifi_missing": False,
            "service_failed": False,
            "unknown_exception": False,
        }

    def set_gpio_error(self, value: bool) -> None:
        self._set_flag("gpio_error", value)

    def set_web_down(self, value: bool) -> None:
        self._set_flag("web_down", value)

    def set_log_export_failure(self, value: bool) -> None:
        self._set_flag("log_export_failure", value)

    def set_wifi_missing(self, value: bool) -> None:
        self._set_flag("wifi_missing", value)

    def set_service_failed(self, value: bool) -> None:
        self._set_flag("service_failed", value)

    def set_unknown_exception(self, value: bool) -> None:
        self._set_flag("unknown_exception", value)

    def set_ready(self) -> None:
        with self._lock:
            for key in self._flags:
                if key != "unknown_exception":
                    self._flags[key] = False
        self._status_led.set_code(StatusCode.READY)

    def _set_flag(self, key: str, value: bool) -> None:
        with self._lock:
            self._flags[key] = value
        self._update_status()

    def _update_status(self) -> None:
        with self._lock:
            flags = dict(self._flags)

        if flags["gpio_error"]:
            self._status_led.set_code(StatusCode.GPIO_ERROR)
        elif flags["web_down"]:
            self._status_led.set_code(StatusCode.WEB_DOWN)
        elif flags["log_export_failure"]:
            self._status_led.set_code(StatusCode.LOG_EXPORT_FAILURE)
        elif flags["wifi_missing"]:
            self._status_led.set_code(StatusCode.WIFI_MISSING)
        elif flags["service_failed"]:
            self._status_led.set_code(StatusCode.SERVICE_FAILED)
        elif flags["unknown_exception"]:
            self._status_led.set_code(StatusCode.UNKNOWN_EXCEPTION)
        else:
            self._status_led.set_code(StatusCode.READY)


class HealthMonitor(threading.Thread):
    def __init__(self, status_manager, web_health, logger) -> None:
        super().__init__(daemon=True)
        self._status_manager = status_manager
        self._web_health = web_health
        self._logger = logger
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        self._logger.info("Health monitor started")
        while not self._stop_event.is_set():
            wifi_ok = check_wifi_connected(self._logger)
            self._status_manager.set_wifi_missing(not wifi_ok)

            web_ok = self._web_health.check()
            self._status_manager.set_web_down(not web_ok)

            time.sleep(config.HEALTH_POLL_SECONDS)


class WebHealth:
    def __init__(self, logger) -> None:
        self._logger = logger

    def check(self) -> bool:
        try:
            connection = http.client.HTTPConnection(
                "127.0.0.1",
                config.WEB_PORT,
                timeout=2,
            )
            connection.request("GET", "/health")
            response = connection.getresponse()
            healthy = response.status == 200
            self._logger.info("Web health check status=%s", response.status)
            return healthy
        except Exception as exc:
            self._logger.warning("Web health check failed: %s", exc)
            return False


def check_wifi_connected(logger) -> bool:
    if shutil.which("iwgetid"):
        result = subprocess.run(
            ["iwgetid", "-r"],
            capture_output=True,
            text=True,
            check=False,
        )
        ssid = result.stdout.strip()
        connected = result.returncode == 0 and bool(ssid)
        logger.info("Wi-Fi check via iwgetid: connected=%s", connected)
        return connected

    operstate_path = "/sys/class/net/wlan0/operstate"
    if os.path.exists(operstate_path):
        try:
            with open(operstate_path, "r", encoding="utf-8") as handle:
                state = handle.read().strip()
            connected = state == "up"
            logger.info("Wi-Fi check via operstate: %s", state)
            return connected
        except OSError as exc:
            logger.warning("Wi-Fi operstate read failed: %s", exc)
            return False

    logger.warning("Wi-Fi check unavailable; assuming disconnected")
    return False
