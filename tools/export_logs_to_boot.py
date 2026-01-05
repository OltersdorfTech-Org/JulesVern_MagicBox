#!/usr/bin/env python3
"""Copy Magic Box logs to the boot partition for Windows access."""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

LOG_DIR = Path("/var/log/julesverne_magicbox")
LOG_FILES = [
    LOG_DIR / "main.log",
    LOG_DIR / "web.log",
]
BOOT_FIRMWARE = Path("/boot/firmware")
BOOT_FALLBACK = Path("/boot")
EXPORT_DIR_NAME = "jv_logs"


def require_root() -> None:
    if os.geteuid() != 0:
        raise PermissionError("This script must be run with sudo.")


def select_boot_root() -> Path:
    if BOOT_FIRMWARE.exists() and os.path.ismount(BOOT_FIRMWARE):
        return BOOT_FIRMWARE
    if BOOT_FALLBACK.exists() and os.path.ismount(BOOT_FALLBACK):
        return BOOT_FALLBACK
    raise FileNotFoundError("No mounted boot partition found at /boot/firmware or /boot.")


def copy_logs(destination: Path) -> list[Path]:
    destination.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    for log_file in LOG_FILES:
        if not log_file.exists():
            continue
        target = destination / log_file.name
        shutil.copy2(log_file, target)
        copied.append(target)
    return copied


def main() -> int:
    try:
        require_root()
        boot_root = select_boot_root()
        export_dir = boot_root / EXPORT_DIR_NAME
        copied = copy_logs(export_dir)
    except (PermissionError, FileNotFoundError, OSError) as exc:
        print(f"Error: {exc}")
        return 1

    print("Logs exported.")
    print(f"Export folder: {export_dir}")
    if copied:
        print("Copied files:")
        for path in copied:
            print(f" - {path.name}")
    else:
        print("No log files were found to copy.")
    print("Copy off the SD card from Windows by opening the boot partition and")
    print("browsing to the jv_logs/ folder.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
