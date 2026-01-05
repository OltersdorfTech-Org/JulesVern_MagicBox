#!/usr/bin/env python3
"""Copy Magic Box logs to the boot partition for Windows access."""
from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(BASE_DIR))

from log_export import build_export_bundle, ensure_writable_export_root, select_boot_root


def main() -> int:
    try:
        boot_root = select_boot_root()
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        return 1

    export_root, warning = ensure_writable_export_root(boot_root)
    export_dir = build_export_bundle(export_root)
    if warning:
        print(f"Warning: {warning}")

    print("Logs exported.")
    print(f"Export folder: {export_dir}")
    print("Copy off the SD card from Windows by opening the boot partition and")
    print("browsing to the jv_logs/ folder.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
