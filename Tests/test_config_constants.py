import os
import sys
import unittest

TEST_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if TEST_ROOT not in sys.path:
    sys.path.insert(0, TEST_ROOT)

from magicbox import config


class ConfigConstantsTests(unittest.TestCase):
    def test_gpio_constants_exist(self) -> None:
        self.assertTrue(hasattr(config, "GPIO_LID_SWITCH"))
        self.assertTrue(hasattr(config, "GPIO_KEY1_SWITCH"))
        self.assertTrue(hasattr(config, "GPIO_KEY2_SWITCH"))
        self.assertTrue(hasattr(config, "GPIO_STATUS_LED"))
        self.assertTrue(hasattr(config, "GPIO_MESSAGE_LED"))
        self.assertTrue(hasattr(config, "GPIO_KEY1_LED"))
        self.assertTrue(hasattr(config, "GPIO_KEY2_LED"))
        self.assertTrue(hasattr(config, "GPIO_MAGIC_LED"))

    def test_log_constants_exist(self) -> None:
        self.assertTrue(hasattr(config, "LOG_DIR"))
        self.assertTrue(hasattr(config, "RUNTIME_LOG_PATH"))
        self.assertTrue(hasattr(config, "INSTALLER_LOG_PATH"))
        self.assertTrue(hasattr(config, "EXPORT_DIR"))


if __name__ == "__main__":
    unittest.main()
