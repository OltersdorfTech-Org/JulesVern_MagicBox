"""Entry point for the Magic Box controller."""

import signal
import sys
import threading

from magicbox import config
from magicbox.gpio_io import GPIOManager, InputPoller
from magicbox.health import HealthMonitor, StatusManager, WebHealth
from magicbox.leds import MagicLedController, StatusLedController, StatusCode
from magicbox.logging_util import setup_logging
from magicbox.log_export import LogExporter
from magicbox.state import StateStore
from magicbox.webui import create_app


class StateController:
    def __init__(self, state_store, gpio, magic_controller, logger) -> None:
        self._state_store = state_store
        self._gpio = gpio
        self._magic_controller = magic_controller
        self._logger = logger
        self._outputs = {
            "message": False,
            "key1": False,
            "key2": False,
        }

    def snapshot(self):
        return self._state_store.snapshot()

    def set_message_received(self, value: bool):
        snapshot = self._state_store.set_message_received(value)
        self._logger.info("Message received set to %s", value)
        self._apply_outputs(snapshot)
        return snapshot

    def set_gpio_enabled(self, value: bool):
        snapshot = self._state_store.set_gpio_enabled(value)
        self._logger.info("GPIO enabled set to %s", value)
        self._apply_outputs(snapshot)
        return snapshot

    def update_inputs(self, lid_open: bool, key1_pressed: bool, key2_pressed: bool):
        snapshot = self._state_store.update_inputs(lid_open, key1_pressed, key2_pressed)
        self._apply_outputs(snapshot)
        return snapshot

    def update_web_state(self, message_received: bool, gpio_enabled: bool):
        snapshot = self._state_store.set_web_state(message_received, gpio_enabled)
        self._logger.info(
            "Web state updated: message=%s gpio_enabled=%s",
            message_received,
            gpio_enabled,
        )
        self._apply_outputs(snapshot)
        return snapshot

    def _apply_outputs(self, snapshot) -> None:
        if not snapshot.gpio_enabled:
            self._magic_controller.set_enabled(False)
            self._set_output("message", False)
            self._set_output("key1", False)
            self._set_output("key2", False)
            return

        self._magic_controller.set_enabled(True)
        self._set_output("message", snapshot.message_received)
        self._set_output("key1", snapshot.key1_pressed)
        self._set_output("key2", snapshot.key2_pressed)

    def _set_output(self, name: str, value: bool) -> None:
        if self._outputs.get(name) != value:
            self._logger.info("Output %s set to %s", name, value)
            self._outputs[name] = value
        self._gpio.set_output(name, value)


def main() -> int:
    logger = setup_logging()

    gpio = GPIOManager()
    status_led = StatusLedController(gpio, logger)
    status_led.set_code(StatusCode.BOOTING)
    status_led.start()

    status_manager = StatusManager(status_led, logger)

    def handle_exception(exc_type, exc, exc_traceback) -> None:
        logger.error("Unhandled exception", exc_info=(exc_type, exc, exc_traceback))
        status_manager.set_unknown_exception(True)

    def handle_thread_exception(args) -> None:
        logger.error("Unhandled thread exception", exc_info=(args.exc_type, args.exc_value, args.exc_traceback))
        status_manager.set_unknown_exception(True)

    sys.excepthook = handle_exception
    threading.excepthook = handle_thread_exception

    if gpio.init_error:
        logger.error("GPIO initialization failed; using fake GPIO")
        status_manager.set_gpio_error(True)

    state_store = StateStore(
        message_received=config.DEFAULT_MESSAGE_RECEIVED,
        gpio_enabled=config.DEFAULT_GPIO_ENABLED,
    )
    magic_controller = MagicLedController(gpio, logger)
    state_controller = StateController(state_store, gpio, magic_controller, logger)

    initial_inputs = gpio.read_inputs()
    state_controller.set_gpio_enabled(config.DEFAULT_GPIO_ENABLED)
    state_controller.set_message_received(config.DEFAULT_MESSAGE_RECEIVED)
    state_controller.update_inputs(
        initial_inputs.lid_open,
        initial_inputs.key1_pressed,
        initial_inputs.key2_pressed,
    )

    def handle_input_change(previous, current) -> None:
        if previous.lid_open != current.lid_open:
            logger.info("Lid state changed: %s", current.lid_open)
        if previous.key1_pressed != current.key1_pressed:
            logger.info("Key1 state changed: %s", current.key1_pressed)
        if previous.key2_pressed != current.key2_pressed:
            logger.info("Key2 state changed: %s", current.key2_pressed)

        snapshot = state_controller.update_inputs(
            current.lid_open,
            current.key1_pressed,
            current.key2_pressed,
        )

        if (
            not previous.lid_open
            and current.lid_open
            and snapshot.message_received
            and snapshot.gpio_enabled
        ):
            magic_controller.trigger()

    input_poller = InputPoller(gpio, handle_input_change, logger)
    input_poller.start()

    web_health = WebHealth(logger)
    health_monitor = HealthMonitor(status_manager, web_health, logger)
    health_monitor.start()

    log_exporter = LogExporter(logger, status_manager)
    app = create_app(state_controller, log_exporter, logger)

    def handle_shutdown(signum, frame) -> None:
        logger.info("Shutdown signal received: %s", signum)
        input_poller.stop()
        health_monitor.stop()
        magic_controller.stop()
        status_led.stop()
        gpio.cleanup()
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    try:
        logger.info("Starting web server on %s:%s", config.WEB_HOST, config.WEB_PORT)
        status_manager.set_ready()
        app.run(host=config.WEB_HOST, port=config.WEB_PORT)
    except Exception as exc:
        logger.exception("Service failed to start: %s", exc)
        status_manager.set_service_failed(True)
        return 1
    finally:
        input_poller.stop()
        health_monitor.stop()
        magic_controller.stop()
        status_led.stop()
        gpio.cleanup()

    return 0


if __name__ == "__main__":
    sys.exit(main())
