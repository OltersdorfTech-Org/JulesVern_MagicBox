"""Log export logic."""

from dataclasses import dataclass
import datetime
import os
import platform
import shutil
import time

from magicbox import config
from magicbox import __version__


@dataclass
class ExportResult:
    success: bool
    message: str


class LogExporter:
    def __init__(self, logger, status_manager) -> None:
        self._logger = logger
        self._status_manager = status_manager

    def export_logs(self) -> ExportResult:
        self._logger.info("Log export requested")
        try:
            os.makedirs(config.EXPORT_DIR, exist_ok=True)
            self._copy_logs()

            manifest_path = os.path.join(config.EXPORT_DIR, "export_manifest.txt")
            with open(manifest_path, "w", encoding="utf-8") as handle:
                handle.write("Magic Box Log Export\n")
                handle.write(f"Timestamp: {datetime.datetime.now().isoformat()}\n")
                handle.write(f"Hostname: {os.uname().nodename}\n")
                handle.write(f"App Version: {__version__}\n")
                handle.write(f"Python Version: {platform.python_version()}\n")

            self._logger.info("Log export completed")
            return ExportResult(success=True, message="Logs exported to /boot/firmware/MAGICBOX_LOGS")
        except Exception as exc:
            self._status_manager.set_log_export_failure(True)
            self._logger.exception("Log export failed: %s", exc)
            time.sleep(2.0)
            return ExportResult(success=False, message="Log export failed; check logs")
        finally:
            self._status_manager.set_log_export_failure(False)

    def _copy_logs(self) -> None:
        copied = False
        for path in _collect_log_paths(config.RUNTIME_LOG_PATH):
            shutil.copy2(path, config.EXPORT_DIR)
            copied = True
        for path in _collect_log_paths(config.INSTALLER_LOG_PATH):
            shutil.copy2(path, config.EXPORT_DIR)
            copied = True
        if not copied:
            raise FileNotFoundError("No log files available to export")


def _collect_log_paths(path: str) -> list[str]:
    if not os.path.exists(path):
        return []
    paths = [path]
    directory = os.path.dirname(path)
    basename = os.path.basename(path)
    for entry in os.listdir(directory):
        if entry.startswith(f"{basename}."):
            candidate = os.path.join(directory, entry)
            if os.path.isfile(candidate):
                paths.append(candidate)
    return paths
