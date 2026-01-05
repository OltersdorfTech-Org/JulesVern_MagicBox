"""Logging helpers for Magic Box services."""
from __future__ import annotations

import logging
import os
import shutil
import socket
import subprocess
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Iterable, Optional

import config

LOG_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_MESSAGE_FORMAT = "%(asctime)s [%(levelname)s] %(name)s (%(module)s:%(lineno)d): %(message)s"


def _ensure_log_dir(log_dir: Path) -> bool:
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return False
    return os.access(log_dir, os.W_OK)


def _parse_level(level: str) -> int:
    return getattr(logging, level.upper(), logging.INFO)


def _fallback_log_dir() -> Path:
    return Path.home() / "julesverne_magicbox_logs"


def get_logger(name: str, log_file: Optional[Path] = None) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(_parse_level(config.LOG_LEVEL))
    logger.propagate = False

    formatter = logging.Formatter(LOG_MESSAGE_FORMAT, datefmt=LOG_FORMAT)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if log_file is not None:
        log_dir = log_file.parent
        if not _ensure_log_dir(log_dir):
            fallback_dir = _fallback_log_dir()
            if _ensure_log_dir(fallback_dir):
                logger.warning(
                    "Log directory %s is not writable; falling back to %s.",
                    log_dir,
                    fallback_dir,
                )
                log_file = fallback_dir / log_file.name
                log_dir = fallback_dir
            else:
                logger.warning(
                    "Log directory %s is not writable; file logging disabled.",
                    log_dir,
                )
                log_file = None

        if log_file is not None:
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=config.LOG_ROTATION_BYTES,
                backupCount=config.LOG_BACKUP_COUNT,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger


def _read_git_commit(repo_root: Path) -> Optional[str]:
    head_path = repo_root / ".git" / "HEAD"
    try:
        content = head_path.read_text(encoding="utf-8").strip()
    except OSError:
        return None

    if content.startswith("ref:"):
        ref_path = repo_root / ".git" / content.split(" ", 1)[1]
        try:
            return ref_path.read_text(encoding="utf-8").strip()
        except OSError:
            return None
    return content


def _collect_ip_addresses() -> Iterable[str]:
    addresses = set()
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None):
            addr = info[4][0]
            if "." in addr and not addr.startswith("127."):
                addresses.add(addr)
    except OSError:
        pass

    try:
        result = subprocess.run(
            ["ip", "-4", "addr", "show"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        result = None

    if result and result.returncode == 0:
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("inet "):
                addr = line.split()[1].split("/")[0]
                if not addr.startswith("127."):
                    addresses.add(addr)

    return sorted(addresses)


def log_startup_banner(logger: logging.Logger, component: str) -> None:
    repo_root = Path(__file__).resolve().parent.parent
    commit = _read_git_commit(repo_root) or "unknown"
    hostname = socket.gethostname()
    ip_addresses = ", ".join(_collect_ip_addresses()) or "unknown"
    disk = shutil.disk_usage("/")
    free_percent = (disk.free / disk.total) * 100
    logger.info(
        "Startup banner | component=%s | version=%s | commit=%s | host=%s | ip=%s | disk_free=%.1f%% | time=%s",
        component,
        config.APP_VERSION,
        commit,
        hostname,
        ip_addresses,
        free_percent,
        datetime.utcnow().isoformat(timespec="seconds") + "Z",
    )
