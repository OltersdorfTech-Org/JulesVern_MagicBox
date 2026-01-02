"""Utilities for exporting logs to a Windows-readable partition."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable, Sequence

import config

BOOT_CANDIDATES = (Path("/boot/firmware"), Path("/boot"))


def select_boot_root(candidates: Sequence[Path] = BOOT_CANDIDATES) -> Path:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("No boot partition found at /boot or /boot/firmware")


def export_logs(
    destination_root: Path,
    log_files: Iterable[Path],
) -> list[Path]:
    destination_root.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    for log_file in log_files:
        source = log_file
        if not source.exists():
            continue
        target = destination_root / source.name
        shutil.copy2(source, target)
        copied.append(target)
    return copied


def default_log_files() -> list[Path]:
    return [config.LOG_FILE_MAIN, config.LOG_FILE_WEB, config.LOG_FILE_GPIO]
