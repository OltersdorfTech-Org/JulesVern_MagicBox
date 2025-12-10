# Magic Lid GPIO Controller (Raspberry Pi Zero 2 W)

A headless Raspberry Pi project that monitors three switches (lid + two keys) and drives four LEDs. The lid LED can also be controlled remotely via SSH commands from the RaspController app while still respecting the physical lid switch. A background Python service (gpiozero-based) keeps LEDs in sync with switch states, persists a remote enable flag, and supports a future "Magic LED" flicker effect once the desired truth table is confirmed.

> ⚠️ Several pin numbers from the original request are ambiguous or electrically invalid. Confirm BCM GPIO pins before wiring (physical pin 1 is 3.3 V and **cannot** be used as a GPIO input).

## I/O Summary

| Signal       | Purpose                          | BCM GPIO | Physical Pin | Status |
|--------------|----------------------------------|----------|--------------|--------|
| LID_SWITCH   | Active-low switch to GND         | 13       | 33           | Confirmed by user |
| KEY1_SWITCH  | Active-low switch to GND         | 23       | 16           | Please confirm |
| KEY2_SWITCH  | Active-low switch to GND         | 5        | 29           | Moved to its own GPIO (update if wired differently) |
| LID_LED      | LED w/ resistor to GND           | 4        | 7            | Please confirm |
| KEY1_LED     | LED w/ resistor to GND           | 24       | 18           | Please confirm |
| KEY2_LED     | LED w/ resistor to GND           | 6        | 31           | Moved to its own GPIO (update if wired differently) |
| MAGIC_LED    | LED w/ resistor to GND (flicker) | 19       | 35           | Please confirm |

## Hardware / Wiring

- **Switches** are active-low: one side to the GPIO pin, the other to GND. No external pull-ups are present; internal pull-ups are enabled in software (`pull_up=True`), so closing the switch pulls the GPIO low.
- **LEDs** are wired from the GPIO pin through an appropriate resistor to GND (active-high in software).
- All pin numbers in the table are physical header pins with BCM mappings listed. If your wiring differs, edit `src/config.py` accordingly.
- Double-check your mapping with an official Raspberry Pi pinout before applying power.

## Software Setup

Tested for Raspberry Pi OS (Bullseye/Bookworm) with Python 3.

1. Update packages: `sudo apt update && sudo apt upgrade -y`
2. Install GPIO dependencies: `sudo apt install -y python3-gpiozero python3-rpi.gpio`
3. Clone/download this repository: `git clone https://github.com/<your-user>/JulesVern_MagicBox.git && cd JulesVern_MagicBox`
4. (Optional) Create a venv, then install pip deps: `pip install -r requirements.txt`
5. **Edit pin mappings and rules:** open `src/config.py` and set BCM pin numbers for all signals (Lid Switch, Key 2 Switch, Key 2 LED, etc.).
6. Run manually: `python3 src/main.py`

## Running the Program

- Manual start: `python3 src/main.py`
- Stop safely: press `Ctrl+C` in the terminal (service traps SIGINT/SIGTERM, turns off LEDs, and cleans GPIO).
- Logs: when run foreground, prints switch events and remote updates. With systemd, view via `journalctl -u magic_lid.service -f`.

## Autostart (systemd)

A sample unit file is provided at `systemd/magic_lid.service`. Update paths if your checkout lives elsewhere.

```sh
sudo cp systemd/magic_lid.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable magic_lid.service
sudo systemctl start magic_lid.service
sudo systemctl status magic_lid.service
# Logs
journalctl -u magic_lid.service -f
```

## RaspController Integration (remote LID LED)

RaspController can run SSH commands. The remote LID LED flag is stored in `state/lid_remote_state.json` and read by the running service.

Examples (replace path if needed):

- Turn remote LID LED **ON**: `python3 /home/pi/JulesVern_MagicBox/src/main.py --set-lid-remote on`
- Turn remote LID LED **OFF**: `python3 /home/pi/JulesVern_MagicBox/src/main.py --set-lid-remote off`
- Toggle remote LID LED: `python3 /home/pi/JulesVern_MagicBox/src/main.py --set-lid-remote toggle`
- Check state: `python3 /home/pi/JulesVern_MagicBox/src/main.py --print-status`

Interaction summary:
- Lid closed **and** remote state ON → LID LED ON
- Lid open → LID LED OFF regardless of remote state

## Configuration

All tunables live in `src/config.py`:
- `SignalPin` entries for each switch/LED (BCM + physical pins, notes, confirmation status).
- `SWITCH_PULL_UP` / `SWITCH_DEBOUNCE_S` for switch behavior.
- `MAGIC_FLICKER_MIN_MS` / `MAGIC_FLICKER_MAX_MS` for flicker timing.
- `MAGIC_FLICKER_RULE` predicate to decide when the Magic LED should flicker (default is **disabled** until clarified).
- `REMOTE_STATE_FILE` path for the remote LID flag.

## Safety Notes

- Never drive LEDs without appropriate resistors.
- Verify every pin assignment (BCM vs. physical) before connecting hardware.
- Physical pin 1 supplies 3.3 V and is **not** a GPIO input—do not wire the lid switch there.

## Open Questions (please confirm)

- Do the proposed BCM mappings match your wiring for KEY1 switch/LED, LID LED, and the relocated KEY2 switch/LED (defaults use BCM5 and BCM6 to give them dedicated pins)?
- Magic LED behavior: provide a truth table—when should it flicker, be off, or be solid?
