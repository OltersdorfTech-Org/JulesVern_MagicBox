"""Log export logic."""

from dataclasses import dataclass
import datetime
import os
import shutil

from magicbox import config


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
            shutil.copy2(config.RUNTIME_LOG_PATH, config.EXPORT_DIR)
            if os.path.exists(config.INSTALLER_LOG_PATH):
                shutil.copy2(config.INSTALLER_LOG_PATH, config.EXPORT_DIR)

            manifest_path = os.path.join(config.EXPORT_DIR, "export_manifest.txt")
            with open(manifest_path, "w", encoding="utf-8") as handle:
                handle.write("Magic Box Log Export\n")
                handle.write(f"Timestamp: {datetime.datetime.now().isoformat()}\n")
                handle.write(f"Hostname: {os.uname().nodename}\n")

            self._logger.info("Log export completed")
            return ExportResult(success=True, message="Logs exported to /boot/firmware/MAGICBOX_LOGS")
        except Exception as exc:
            self._status_manager.set_log_export_failure(True)
            self._logger.exception("Log export failed: %s", exc)
            return ExportResult(success=False, message="Log export failed; check logs")
        finally:
            self._status_manager.set_log_export_failure(False)
