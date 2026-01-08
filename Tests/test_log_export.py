import logging
import os
import sys
import tempfile
import unittest
from unittest import mock

TEST_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if TEST_ROOT not in sys.path:
    sys.path.insert(0, TEST_ROOT)

from magicbox import config
from magicbox.log_export import LogExporter


class FakeStatusManager:
    def __init__(self) -> None:
        self.calls = []

    def set_log_export_failure(self, value: bool) -> None:
        self.calls.append(value)


class LogExportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.logger = logging.getLogger("magicbox.test.log_export")
        self.logger.handlers.clear()
        self.logger.addHandler(logging.NullHandler())

    def test_export_creates_manifest_and_copies_logs(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            export_dir = os.path.join(tempdir, "MAGICBOX_LOGS")
            runtime_log = os.path.join(tempdir, "magicbox.log")
            installer_log = os.path.join(tempdir, "installer.log")

            with open(runtime_log, "w", encoding="utf-8") as handle:
                handle.write("runtime log")
            with open(installer_log, "w", encoding="utf-8") as handle:
                handle.write("installer log")

            status_manager = FakeStatusManager()
            exporter = LogExporter(self.logger, status_manager)

            with mock.patch.object(config, "EXPORT_DIR", export_dir), \
                mock.patch.object(config, "RUNTIME_LOG_PATH", runtime_log), \
                mock.patch.object(config, "INSTALLER_LOG_PATH", installer_log), \
                mock.patch("magicbox.log_export.os.makedirs", wraps=os.makedirs) as makedirs:
                result = exporter.export_logs()

            self.assertTrue(result.success)
            makedirs.assert_called_with(export_dir, exist_ok=True)
            self.assertTrue(os.path.exists(os.path.join(export_dir, "magicbox.log")))
            self.assertTrue(os.path.exists(os.path.join(export_dir, "installer.log")))
            self.assertTrue(os.path.exists(os.path.join(export_dir, "export_manifest.txt")))


if __name__ == "__main__":
    unittest.main()
