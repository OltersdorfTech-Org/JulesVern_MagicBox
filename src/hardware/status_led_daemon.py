"""Status LED daemon for Magic Box fault monitoring."""

from __future__ import annotations

import shutil
import signal
import socket
import subprocess
import time
from threading import Thread
from pathlib import Path
from typing import Iterable, Optional, Tuple

from status_led import StatusLED

GPIO_PIN = 12
DISK_FREE_THRESHOLD_PERCENT = 5.0
INTERNET_CHECK_TARGETS: Iterable[Tuple[str, int]] = (
    ("1.1.1.1", 443),
    ("8.8.8.8", 53),
)
INTERNET_TIMEOUT_S = 2.0
MAIN_SERVICE_NAME = "magic_lid.service"
CHECK_INTERVAL_S = 2.0
WLAN_INTERFACE = "wlan0"

PATTERNS = {
    "booting": [(True, 0.5), (False, 0.5)],
    "fault_service": [(True, 0.15), (False, 0.15), (True, 0.15), (False, 1.2)],
    "fault_wifi": [
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
        (False, 1.2),
    ],
}


def log(message: str) -> None:
    print(f"[status-led] {message}")


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
        log(f"Command not found: {' '.join(command)}")
        return None
    except subprocess.TimeoutExpired:
        log(f"Command timed out: {' '.join(command)}")
        return None
    if result.returncode != 0:
        stderr = result.stderr.strip()
        if stderr:
            log(f"Command failed ({' '.join(command)}): {stderr}")
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
    if not output:
        return None
    return output


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
    return free_percent < DISK_FREE_THRESHOLD_PERCENT


def service_state() -> str:
    output = _command_output(["systemctl", "is-active", MAIN_SERVICE_NAME], timeout=2.0)
    return output or "unknown"


def select_led_mode() -> str:
    if disk_low():
        return "fault_disk"

    state = service_state()
    if state not in ("active", "activating"):
        return "fault_service"

    wifi_ok = wifi_connected()
    if not wifi_ok:
        return "fault_wifi"

    if not internet_available():
        return "fault_internet"

    if state == "active":
        return "ready"
    return "booting"


def main() -> None:
    led = StatusLED(GPIO_PIN, log=log)

    def _handle_signal(_signum, _frame):
        log("Received stop signal; shutting down.")
        led.stop()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    log("Status LED daemon starting.")
    led.set_mode("booting")

    led_thread = Thread(target=led.run, args=(PATTERNS,), daemon=True)
    led_thread.start()

    try:
        while not led.stopped():
            try:
                mode = select_led_mode()
                led.set_mode(mode)
            except Exception as exc:  # noqa: BLE001 - log and continue to avoid silent failures
                log(f"Error while evaluating LED state: {exc}")
            time.sleep(CHECK_INTERVAL_S)
    finally:
        led.stop()
        led_thread.join(timeout=2.0)
        log("Status LED daemon exiting.")


if __name__ == "__main__":
    main()
