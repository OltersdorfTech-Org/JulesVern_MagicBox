"""Helpers for ensuring runtime filesystem paths exist."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import logging


def _ensure_dir(path: Path, logger: logging.Logger, label: str) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        logger.error("Failed to create %s directory %s: %s", label, path, exc)
        return False
    if not os.access(path, os.W_OK):
        logger.error("No write permission for %s directory %s.", label, path)
        return False
    return True


def ensure_runtime_dirs(
    logger: logging.Logger,
    log_dir: Path,
    state_dir: Optional[Path] = None,
) -> bool:
    if not _ensure_dir(log_dir, logger, "log"):
        return False
    if state_dir is not None and not _ensure_dir(state_dir, logger, "state"):
        return False
    return True
