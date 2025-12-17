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

## Software Setup

Tested for Raspberry Pi OS (Bullseye/Bookworm) with Python 3.

1. Update packages: `sudo apt update && sudo apt upgrade -y`
2. Install GPIO dependencies: `sudo apt install -y python3-gpiozero python3-rpi.gpio`
3. If working on Windows 10/11 without WSL, download the repo ZIP from GitHub, extract it, and copy the **JulesVern_MagicBox** folder to the SD card’s `boot`/`firmware` partition using File Explorer (see "Windows-only: copy the repo without Git" below). No Git is required on the Pi.
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

SSH commands remain supported for power users (or RaspController custom commands), but the web UI below is the simplest option for day-to-day control.

## Web UI (Flask) — big buttons on a web page

Intent: provide a dead-simple, mobile-friendly way to flip the remote LID LED flag from any browser on your trusted home network. The web UI reuses the same stored flag that the background GPIO controller watches, so hardware behavior stays unchanged.

### Dependencies

- Install pip if needed: `sudo apt install python3-pip`
- Install Flask (adds to the existing gpiozero dependency):

```sh
pip3 install -r requirements.txt
# or
pip3 install flask
```

### Web UI overview

- Once running, open `http://<pi-ip>:8080`.
- You will see two toggle buttons with indicators beside them:
  - **LID LED Toggle** — flips the stored remote LID flag.
  - **magic flicker toggle** — flips the Magic Flag controlling the Magic LED flicker permission.
- A prominent **Safety** control appears above the toggles. Safety defaults to **OFF** on boot; when it is off, the toggles are disabled and the server rejects toggle actions. Enable Safety to allow any GPIO activity.
- Status text shows the lid switch state (OPEN/CLOSED/Unknown).
- Intended for local, trusted networks only; no authentication is provided.

### How to run the web UI manually

```sh
cd /home/pi/JulesVern_MagicBox
python3 src/web_server.py  # defaults to port 8080
```

Then browse to `http://<pi-ip>:8080`. Use `hostname -I` on the Pi to print its LAN IP address.

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

### Optional systemd setup for the web UI

Keep the original GPIO controller service enabled. Add a separate unit for the Flask server so both can run together:

```sh
sudo cp systemd/magic_lid_web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable magic_lid_web.service
sudo systemctl start magic_lid_web.service
sudo systemctl status magic_lid_web.service
```

After that, powering on the Pi and visiting `http://<pi-ip>:8080` is enough—tap a button and the background controller will pick up the new flag immediately.

### Why this design & assumptions

- Reuses the existing `state/lid_remote_state.json` file, adding Magic and Safety flags alongside the remote LID flag.
- The Flask server only adjusts stored flags, enforces Safety in the routes, and reads the lid switch if possible; it does not drive LEDs directly.
- Designed for a trusted home LAN (no authentication or TLS); if you need wider exposure, place it behind your own secure reverse proxy.

## Windows-only: copy the repo without Git

If you do not want to install Git on Windows, you can prepare the SD card entirely from File Explorer:

1. Download the repository ZIP from GitHub on your Windows PC.
2. Insert the Raspberry Pi SD card. Windows should mount the FAT `boot`/`firmware` partition automatically. If it does not, open **Disk Management**, right-click the small FAT partition for the SD card, and assign it a drive letter so it appears in File Explorer.
3. Extract the ZIP and copy the `JulesVern_MagicBox` folder into the root of the `boot`/`firmware` drive.
4. Safely eject the card and boot the Pi.

### Move the copied folder on the Pi and run it

After the Pi boots (with the card prepared above), move the project into your home directory and run setup from there:

```sh
cd /home/pi
mkdir -p ~/src
mv /boot/firmware/JulesVern_MagicBox ~/src/
cd ~/src/JulesVern_MagicBox
python3 -m venv .venv  # optional
source .venv/bin/activate || true
pip install -r requirements.txt
python3 src/main.py
```

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
