# Magic Lid GPIO Controller (Raspberry Pi Zero 2 W)

Headless Raspberry Pi project that watches three switches (lid + two keys) and drives four LEDs. A background Python service (gpiozero-based) keeps LEDs in sync with switch states, persists a remote enable flag, and exposes a web UI for toggling the remote LID and Magic flicker flags.

> ⚠️ Confirm BCM GPIO pins before wiring (physical pin 1 is 3.3 V and **cannot** be used as a GPIO input).

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

```
Raspberry Pi 40-pin header (physical numbers)

 3V3  (1) (2)  5V
 GPIO2 (3) (4)  5V
 GPIO3 (5) (6) GND
 GPIO4 (7) (8) GPIO14
  GND  (9) (10) GPIO15
 GPIO17(11) (12) GPIO18
 GPIO27(13) (14) GND
 GPIO22(15) (16) GPIO23
 3V3  (17) (18) GPIO24
 GPIO10(19) (20) GND
 GPIO9 (21) (22) GPIO25
 GPIO11(23) (24) GPIO8
  GND  (25) (26) GPIO7
 GPIO0 (27) (28) GPIO1
 GPIO5 (29) (30) GND
 GPIO6 (31) (32) GPIO12
 GPIO13(33) (34) GND
 GPIO19(35) (36) GPIO16
 GPIO26(37) (38) GPIO20
  GND  (39) (40) GPIO21
```

## Install (Bookworm, Pi Zero 2 W)

Installer tasks: copies the repo to the target user’s home, ensures writable state/config paths, creates a Python venv, installs dependencies, writes systemd units, and drops a desktop launcher that opens the web UI.

**Windows SD card method (no Git)**
1. Download the repo ZIP on Windows and extract it.
2. Copy the `JulesVern_MagicBox` folder onto the SD card’s `boot`/`firmware` partition.
3. Boot the Pi with that card, open Terminal, and run:
   ```sh
   sudo /boot/firmware/JulesVern_MagicBox/sdcard_bootstrap/install.sh
   ```
   - The installer copies the project to `/home/<user>/JulesVern_MagicBox` (override with `MAGICBOX_TARGET=/path`), fixes ownership, and installs services.

**Already on the Pi**
1. From the checkout directory:
   ```sh
   sudo ./INSTALL_MAGIC_BOX.sh
   ```
   - Re-runnable; refreshes dependencies and services. To force a different target path or user, set `MAGICBOX_TARGET=/path` and/or `MAGICBOX_USER=<user>` when invoking.

**What you get after install**
- Services:
  - `magic_lid.service` (GPIO controller) enabled and started.
  - `magic_lid_web.service` (Flask web UI) installed, not auto-enabled; enable with `sudo systemctl enable --now magic_lid_web.service`.
- Helper CLI: `magicbox status|logs|start|stop|restart|install`.
- Desktop launcher: `Magic Lid Web Remote.desktop` on the target user’s Desktop opens `http://localhost:<port>` (default 8080; override with `MAGICBOX_WEB_PORT`).
- Writable state/config under the copied repo (e.g., `/home/<user>/JulesVern_MagicBox/state/lid_remote_state.json`), avoiding permission issues on `/boot/firmware`.

See [`docs/INSTALL_PI_ZERO_2W.md`](docs/INSTALL_PI_ZERO_2W.md) for troubleshooting.

### Manual run (no systemd)
- Edit pin mappings and rules in `src/config.py`.
- Run: `python3 src/main.py`

## Running & logs

- Foreground: `python3 src/main.py`
- Stop: `Ctrl+C` (service traps SIGINT/SIGTERM and cleans up GPIO).
- Logs (systemd): `journalctl -u magic_lid.service -f`
- Status: `sudo systemctl status magic_lid.service` or `magicbox status`

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

SSH commands remain supported for power users (or RaspController custom commands), but the web UI below is the simplest option for day-to-day control.

## Web UI (Flask) — big buttons on a web page

Intent: provide a dead-simple, mobile-friendly way to flip the remote LID LED flag from any browser on your trusted home network. The web UI reuses the same stored flag that the background GPIO controller watches, so hardware behavior stays unchanged.

### Web UI overview

- Start (systemd): `sudo systemctl enable --now magic_lid_web.service` or run manually:
  ```sh
  cd /home/pi/JulesVern_MagicBox
  python3 src/web_server.py --port 8080
  ```
- Open `http://<pi-ip>:8080` (launcher uses `localhost`).
- Controls:
  - **Safety** — must be ON to allow any GPIO output. When OFF, toggles are disabled and outputs stay off.
  - **LID LED Toggle** — flips the stored remote LID flag.
  - **magic flicker toggle** — flips the Magic flicker flag.
- Status shows lid switch state and current pin mapping. Intended for trusted LAN only (no auth/TLS).

### GPIO table from the web UI

- The bottom of the page includes a table to edit the physical pin numbers for:
  - `lid_switch_pin`
  - `lid_led_pin`
  - `magic_flicker_led_pin`
  - `Key1LED PIN`
  - `Key2LED PIN`
  - `Key1switch PIN`
  - `Key2switch PIN`
- Inputs must be integers mapped to real GPIO header pins; power/ground pins are rejected. Submitted values rewrite the dataclass entries in `src/config.py`.
- The Raspberry Pi physical pin diagram (above) is rendered alongside the form to help pick the right header numbers.

After enabling the web service, visiting `http://<pi-ip>:8080` lets you toggle flags; the background GPIO controller picks them up immediately.

### Why this design & assumptions

- Uses a writable repo location under the target user’s home to avoid FAT partition permission errors.
- Web server edits `src/config.py` and `state/lid_remote_state.json` within that location; systemd services run as the target user for consistent permissions.
- Trusted LAN only; place behind your own secure reverse proxy if exposing externally.

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
