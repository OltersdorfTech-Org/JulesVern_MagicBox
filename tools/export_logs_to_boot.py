#!/usr/bin/env python3
"""Copy Magic Box logs to the boot partition for Windows access."""
from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(BASE_DIR))

import config
from log_export import default_log_files, export_logs, select_boot_root


def main() -> int:
    try:
        boot_root = select_boot_root()
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        return 1

    destination = boot_root / "jv_logs"
    log_files = default_log_files()
    copied = export_logs(destination, log_files)
    if not copied:
        print(f"No log files found in {config.LOG_DIR}.")
        print(f"Destination folder created at {destination} (if possible).")
        return 0

    print("Copied logs:")
    for path in copied:
        print(f"- {path}")
    print(f"Logs exported to {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
