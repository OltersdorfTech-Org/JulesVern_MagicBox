import os
import unittest


class ImportTests(unittest.TestCase):
    def setUp(self):
        os.environ["MAGICBOX_FORCE_FAKE_GPIO"] = "1"

    def test_import_core_modules(self):
        import magicbox.config
        import magicbox.gpio_io
        import magicbox.health
        import magicbox.leds
        import magicbox.log_export
        import magicbox.logging_util
        import magicbox.state
        import magicbox.webui

        self.assertTrue(hasattr(magicbox.config, "GPIO_LID_SWITCH"))


if __name__ == "__main__":
    unittest.main()
