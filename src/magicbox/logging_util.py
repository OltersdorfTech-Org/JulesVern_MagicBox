"""Logging utilities for the Magic Box."""

import logging
import logging.handlers
import os

from magicbox import config

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging() -> logging.Logger:
    os.makedirs(config.LOG_DIR, exist_ok=True)

    logger = logging.getLogger("magicbox")
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)

    file_handler = logging.handlers.RotatingFileHandler(
        config.RUNTIME_LOG_PATH,
        maxBytes=config.LOG_MAX_BYTES,
        backupCount=config.LOG_BACKUP_COUNT,
    )
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.handlers.clear()
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.propagate = False

    logger.info("Logging initialized")
    return logger
