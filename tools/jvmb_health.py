#!/usr/bin/env python3
"""Basic health check for Magic Box services."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(BASE_DIR))

import config

MAIN_SERVICE = "magic_lid.service"
WEB_SERVICE = "magic_lid_web.service"


def _run(command: list[str]) -> str:
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=4,
        )
    except FileNotFoundError:
        return f"Command not found: {command[0]}"
    except subprocess.TimeoutExpired:
        return "Command timed out"
    output = (result.stdout.strip() or result.stderr.strip() or "").strip()
    return output


def service_status(service: str) -> str:
    return _run(["systemctl", "is-active", service])


def tail_log(path: Path, lines: int = 20) -> str:
    if not path.exists():
        return f"Log file not found: {path}"
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            content = handle.readlines()
    except OSError as exc:
        return f"Unable to read log file: {exc}"
    return "".join(content[-lines:]).strip()


def wifi_status() -> str:
    ssid = _run(["iwgetid", "-r"])
    if ssid and not ssid.startswith("Command"):
        return f"SSID: {ssid}"
    nmcli = _run(["nmcli", "-t", "-f", "ACTIVE,SSID", "dev", "wifi"])
    if nmcli and "yes:" in nmcli:
        for line in nmcli.splitlines():
            if line.startswith("yes:"):
                return f"SSID: {line.split('yes:', 1)[1]}"
    return "Wi-Fi: not connected"


def internet_status() -> str:
    result = _run(["ping", "-c", "1", "-W", "2", "1.1.1.1"])
    if "1 received" in result or "1 packets received" in result:
        return "Internet: reachable"
    return f"Internet: unreachable ({result or 'no ping response'})"


def disk_status() -> str:
    usage = shutil.disk_usage("/")
    free_percent = (usage.free / usage.total) * 100
    return f"Disk free: {free_percent:.1f}%"


def main() -> int:
    print("Magic Box Health Check")
    print("=======================")
    print(f"Main service ({MAIN_SERVICE}): {service_status(MAIN_SERVICE)}")
    print(f"Web service ({WEB_SERVICE}): {service_status(WEB_SERVICE)}")
    print(f"{wifi_status()}")
    print(f"{internet_status()}")
    print(f"{disk_status()}")
    print("\nLast 20 journal lines (main service):")
    print(_run(["journalctl", "-u", MAIN_SERVICE, "-n", "20", "--no-pager"]))
    print("\nLast 20 lines from main.log:")
    print(tail_log(config.LOG_FILE_MAIN))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
