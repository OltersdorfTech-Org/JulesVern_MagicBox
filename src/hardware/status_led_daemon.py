"""Status LED daemon for Magic Box fault monitoring."""

from __future__ import annotations

import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from threading import Thread
from typing import Iterable, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

import config
import logging_utils
from status_led import StatusLED

GPIO_PIN = 12
INTERNET_CHECK_TARGETS: Iterable[Tuple[str, int]] = (
    ("1.1.1.1", 443),
    ("8.8.8.8", 53),
)
INTERNET_TIMEOUT_S = 2.0
MAIN_SERVICE_NAME = "magic_lid.service"
WEB_SERVICE_NAME = "magic_lid_web.service"
CHECK_INTERVAL_S = 2.0
WLAN_INTERFACE = "wlan0"

PATTERNS = {
    "booting": [(True, 0.5), (False, 0.5)],
    "fault_service": [(True, 0.15), (False, 0.15), (True, 0.15), (False, 1.2)],
    "fault_web": [
        (True, 0.15),
        (False, 0.15),
        (True, 0.15),
        (False, 0.15),
        (True, 0.15),
        (False, 1.2),
    ],
    "fault_wifi": [
        (True, 0.15),
        (False, 0.15),
        (True, 0.15),
        (False, 0.15),
        (True, 0.15),
        (False, 0.15),
        (True, 0.15),
        (False, 1.2),
    ],
    "fault_internet": [
        (True, 0.15),
        (False, 0.15),
        (True, 0.15),
        (False, 0.15),
        (True, 0.15),
        (False, 0.15),
        (True, 0.15),
        (False, 0.15),
        (True, 0.15),
        (False, 1.2),
    ],
    "fault_disk": [
        (True, 0.15),
        (False, 0.15),
        (True, 0.15),
        (False, 0.15),
        (True, 0.15),
        (False, 0.15),
        (True, 0.15),
        (False, 0.15),
        (True, 0.15),
        (False, 0.15),
        (True, 0.15),
        (False, 1.2),
    ],
}

logger = logging_utils.get_logger("magicbox.status_led", config.LOG_FILE_GPIO)


def _command_output(command: list[str], timeout: float = 2.0) -> Optional[str]:
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        logger.warning("Command not found: %s", " ".join(command))
        return None
    except subprocess.TimeoutExpired:
        logger.warning("Command timed out: %s", " ".join(command))
        return None
    if result.returncode != 0:
        stderr = result.stderr.strip()
        if stderr:
            logger.warning("Command failed (%s): %s", " ".join(command), stderr)
        return None
    return result.stdout.strip()


def _wifi_interface_exists() -> bool:
    return Path(f"/sys/class/net/{WLAN_INTERFACE}").exists()


def _wifi_has_ipv4() -> bool:
    output = _command_output(["ip", "-4", "addr", "show", "dev", WLAN_INTERFACE])
    if not output:
        return False
    return "inet " in output


def _wifi_ssid() -> Optional[str]:
    output = _command_output(["iwgetid", "-r"])
    if output:
        return output
    output = _command_output(["nmcli", "-t", "-f", "ACTIVE,SSID", "dev", "wifi"])
    if not output:
        return None
    for line in output.splitlines():
        if line.startswith("yes:"):
            return line.split("yes:", 1)[1]
    return None


def wifi_connected() -> bool:
    if not _wifi_interface_exists():
        return False
    if not _wifi_has_ipv4():
        return False
    ssid = _wifi_ssid()
    return bool(ssid)


def internet_available() -> bool:
    for host, port in INTERNET_CHECK_TARGETS:
        try:
            with socket.create_connection((host, port), timeout=INTERNET_TIMEOUT_S):
                return True
        except OSError:
            continue
    return False


def disk_low() -> bool:
    usage = shutil.disk_usage("/")
    free_percent = (usage.free / usage.total) * 100
    free_gb = usage.free / (1024 ** 3)
    return (
        free_percent < config.DISK_FREE_THRESHOLD_PERCENT
        or free_gb < config.DISK_FREE_THRESHOLD_GB
    )


def service_state(service_name: str) -> str:
    output = _command_output(["systemctl", "is-active", service_name], timeout=2.0)
    return output or "unknown"


def decide_mode(
    main_state: str,
    web_state: str,
    wifi_ok: bool,
    internet_ok: bool,
    disk_ok: bool,
) -> tuple[str, str]:
    if main_state not in ("active", "activating"):
        return "fault_service", f"{MAIN_SERVICE_NAME} state={main_state}"
    if web_state not in ("active", "activating"):
        return "fault_web", f"{WEB_SERVICE_NAME} state={web_state}"
    if not disk_ok:
        return "fault_disk", "Disk free below threshold"
    if not wifi_ok:
        return "fault_wifi", "Wi-Fi disconnected"
    if not internet_ok:
        return "fault_internet", "Internet unreachable"
    if main_state == "active":
        return "ready", "Main service active"
    return "booting", "Main service activating"


def select_led_mode() -> tuple[str, str]:
    main_state = service_state(MAIN_SERVICE_NAME)
    web_state = service_state(WEB_SERVICE_NAME)
    wifi_ok = wifi_connected()
    internet_ok = internet_available()
    disk_ok = not disk_low()
    return decide_mode(main_state, web_state, wifi_ok, internet_ok, disk_ok)


def main() -> None:
    led = StatusLED(GPIO_PIN, log=logger.info)

    def _handle_signal(_signum, _frame):
        logger.info("Received stop signal; shutting down.")
        led.stop()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    logger.info("Status LED daemon starting.")
    logging_utils.log_startup_banner(logger, "status_led")
    led.set_mode("booting")

    led_thread = Thread(target=led.run, args=(PATTERNS,), daemon=True)
    led_thread.start()

    try:
        last_mode = None
        while not led.stopped():
            try:
                mode, reason = select_led_mode()
                led.set_mode(mode)
                if mode != last_mode:
                    if mode.startswith("fault"):
                        logger.error("Status LED fault: %s", reason)
                    else:
                        logger.info("Status LED mode reason: %s", reason)
                    last_mode = mode
            except Exception as exc:  # noqa: BLE001 - log and continue to avoid silent failures
                logger.exception("Error while evaluating LED state: %s", exc)
            time.sleep(CHECK_INTERVAL_S)
    finally:
        led.stop()
        led_thread.join(timeout=2.0)
        logger.info("Status LED daemon exiting.")


if __name__ == "__main__":
    main()
