"""GPIO input/output handling."""

from dataclasses import dataclass
import importlib
import importlib.util
import os
import threading
import time
from typing import Callable, Dict

from magicbox import config


@dataclass(frozen=True)
class InputState:
    lid_open: bool
    key1_pressed: bool
    key2_pressed: bool


class GPIOInterface:
    def read_inputs(self) -> InputState:
        raise NotImplementedError

    def set_output(self, name: str, value: bool) -> None:
        raise NotImplementedError

    def cleanup(self) -> None:
        raise NotImplementedError


class FakeGPIO(GPIOInterface):
    def __init__(self) -> None:
        self._inputs = {
            "lid": False,
            "key1": False,
            "key2": False,
        }
        self._outputs: Dict[str, bool] = {
            "status": False,
            "message": False,
            "key1": False,
            "key2": False,
            "magic": False,
        }
        self._lock = threading.Lock()

    def set_input(self, name: str, value: bool) -> None:
        with self._lock:
            self._inputs[name] = value

    def read_inputs(self) -> InputState:
        with self._lock:
            return InputState(
                lid_open=self._inputs["lid"],
                key1_pressed=self._inputs["key1"],
                key2_pressed=self._inputs["key2"],
            )

    def set_output(self, name: str, value: bool) -> None:
        with self._lock:
            self._outputs[name] = value

    def cleanup(self) -> None:
        return


class GPIOZero(GPIOInterface):
    def __init__(self) -> None:
        gpiozero = importlib.import_module("gpiozero")

        self._lid = gpiozero.Button(
            config.GPIO_LID_SWITCH,
            pull_up=True,
            bounce_time=config.DEBOUNCE_SECONDS,
        )
        self._key1 = gpiozero.Button(
            config.GPIO_KEY1_SWITCH,
            pull_up=True,
            bounce_time=config.DEBOUNCE_SECONDS,
        )
        self._key2 = gpiozero.Button(
            config.GPIO_KEY2_SWITCH,
            pull_up=True,
            bounce_time=config.DEBOUNCE_SECONDS,
        )

        self._status_led = gpiozero.LED(config.GPIO_STATUS_LED)
        self._message_led = gpiozero.LED(config.GPIO_MESSAGE_LED)
        self._key1_led = gpiozero.LED(config.GPIO_KEY1_LED)
        self._key2_led = gpiozero.LED(config.GPIO_KEY2_LED)
        self._magic_led = gpiozero.LED(config.GPIO_MAGIC_LED)

        self._output_map = {
            "status": self._status_led,
            "message": self._message_led,
            "key1": self._key1_led,
            "key2": self._key2_led,
            "magic": self._magic_led,
        }

    def read_inputs(self) -> InputState:
        return InputState(
            lid_open=self._lid.is_pressed,
            key1_pressed=self._key1.is_pressed,
            key2_pressed=self._key2.is_pressed,
        )

    def set_output(self, name: str, value: bool) -> None:
        led = self._output_map[name]
        if value:
            led.on()
        else:
            led.off()

    def cleanup(self) -> None:
        for led in self._output_map.values():
            led.off()


class GPIOManager:
    def __init__(self) -> None:
        self.using_fake = False
        self.init_error = False
        self._gpio = None
        force_fake = os.environ.get("MAGICBOX_FORCE_FAKE_GPIO") == "1"

        if force_fake:
            self.using_fake = True
            self._gpio = FakeGPIO()
            return

        spec = importlib.util.find_spec("gpiozero")
        if spec is None:
            self.using_fake = True
            self.init_error = True
            self._gpio = FakeGPIO()
            return

        try:
            self._gpio = GPIOZero()
        except Exception:
            self.using_fake = True
            self.init_error = True
            self._gpio = FakeGPIO()

    def read_inputs(self) -> InputState:
        return self._gpio.read_inputs()

    def set_output(self, name: str, value: bool) -> None:
        self._gpio.set_output(name, value)

    def cleanup(self) -> None:
        self._gpio.cleanup()


class InputPoller(threading.Thread):
    def __init__(
        self,
        gpio: GPIOManager,
        callback: Callable[[InputState, InputState], None],
        logger,
    ) -> None:
        super().__init__(daemon=True)
        self._gpio = gpio
        self._callback = callback
        self._logger = logger
        self._stop_event = threading.Event()
        initial = gpio.read_inputs()
        self._stable_state = initial
        self._last_seen = initial
        now = time.monotonic()
        self._last_change = {name: now for name in ("lid", "key1", "key2")}

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        self._logger.info("Input poller started")
        while not self._stop_event.is_set():
            current = self._gpio.read_inputs()
            last_seen = {
                "lid": self._last_seen.lid_open,
                "key1": self._last_seen.key1_pressed,
                "key2": self._last_seen.key2_pressed,
            }
            stable = {
                "lid": self._stable_state.lid_open,
                "key1": self._stable_state.key1_pressed,
                "key2": self._stable_state.key2_pressed,
            }
            current_map = {
                "lid": current.lid_open,
                "key1": current.key1_pressed,
                "key2": current.key2_pressed,
            }

            now = time.monotonic()
            for key, value in current_map.items():
                if value != last_seen[key]:
                    last_seen[key] = value
                    self._last_change[key] = now

            changed = False
            for key, value in current_map.items():
                if (
                    value != stable[key]
                    and value == last_seen[key]
                    and now - self._last_change[key] >= config.DEBOUNCE_SECONDS
                ):
                    stable[key] = value
                    changed = True

            if changed:
                previous = self._stable_state
                new_state = InputState(
                    lid_open=stable["lid"],
                    key1_pressed=stable["key1"],
                    key2_pressed=stable["key2"],
                )
                self._stable_state = new_state
                self._callback(previous, new_state)

            self._last_seen = InputState(
                lid_open=last_seen["lid"],
                key1_pressed=last_seen["key1"],
                key2_pressed=last_seen["key2"],
            )

            time.sleep(config.POLL_INTERVAL_SECONDS)
