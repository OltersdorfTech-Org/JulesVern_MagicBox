# Magic Lid GPIO Controller (Raspberry Pi Zero 2 W)

![Codex](https://img.shields.io/badge/codex-enabled-blue)
![Python](https://img.shields.io/badge/python-3.x-blue?logo=python&logoColor=white)
![Tests](https://img.shields.io/badge/tests-in%20progress-yellow)
![Version](https://img.shields.io/badge/version-unknown-lightgrey)

Headless-ready Raspberry Pi project that watches three switches (lid + two keys), drives four LEDs, and exposes a web UI for toggling the remote LID and Magic flicker flags. The installer now makes the Pi boot straight into both services with no manual `systemctl` steps, while also dropping a desktop launcher for optional debugging.

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

- **Switches** are active-low: one side to the GPIO pin, the other to GND. Internal pull-ups are enabled (`pull_up=True`).
- **LEDs** are wired from the GPIO pin through a resistor to GND (active-high in software).
- Pin numbers above are physical header pins with BCM mappings listed. If your wiring differs, edit `src/config.py` or use the web UI pin editor.
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

## Quick install (headless boot, Raspberry Pi OS Bookworm)

The installer is idempotent. Re-running it refreshes the venv, services, and desktop launcher.

### Option A: Run from a checkout already on the Pi
```sh
cd /path/to/JulesVern_MagicBox
sudo ./install.sh
```

### Option B: Windows SD card method (no Git on the Pi)
1. On Windows, download the repository ZIP and extract it.
2. Copy the entire `JulesVern_MagicBox` folder onto the SD card’s boot/firmware partition.
3. Boot the Pi, open Terminal, and run:
   ```sh
   sudo /boot/firmware/JulesVern_MagicBox/sdcard_bootstrap/install.sh
   ```

### What the installer does
- Copies the repo to **`/opt/julesvern`** (override with `MAGICBOX_TARGET=/some/path`).
- Creates/uses a dedicated **`julesvern`** system user (override with `MAGICBOX_USER=<user>`); adds it to the `gpio` group.
- Creates a Python venv at `<install>/venv` and installs `requirements.txt`.
- Creates writable data at **`/var/lib/julesvern`** (override with `MAGICBOX_DATA_DIR`); persists the remote state file there.
- Writes and enables **both** systemd units: `magic_lid.service` (GPIO) and `magic_lid_web.service` (Flask UI). They start on boot, restart on failure, and log to journald.
- Reloads systemd, enables, and starts services immediately—no manual `systemctl enable` required.
- Installs helper CLI `magicbox` and a desktop launcher (`Magic Lid Web Remote.desktop`) for the launcher user (defaults to the invoking sudo user, usually `pi`).

## Runtime behavior

- **Autostart on boot:** both services start headlessly after networking is ready; no login or GUI needed.
- **Web UI:** available at `http://<pi-ip>:8080` by default (override during install with `MAGICBOX_WEB_PORT=<port>`).
- **Data & config:** remote state lives at `/var/lib/julesvern/state/lid_remote_state.json`. Pin mappings and other tunables remain in `src/config.py` within `/opt/julesvern` (or your chosen install path).
- **Logging:** all output goes to journald. Follow logs with `journalctl -u magic_lid.service -u magic_lid_web.service -u jv-status-led.service -f`.
- **Restart policy:** `Restart=on-failure` with a 2s backoff on both units.

## Web UI

The web UI provides large touch-friendly controls for safety, shutdown, and GPIO configuration.
Binary assets are not stored in this repository, so screenshots are not embedded here. To capture
one locally, run the web server and use your preferred screenshot tool.

## Status LED (GPIO12)

**Intent:** expose a single external LED that tells you when the system is booting, ready, or in a fault state.

### Wiring
- **GPIO12 → resistor (330Ω–1kΩ) → LED anode**, LED cathode → **GND**.
- BCM numbering only. GPIO12 is physical pin 32.

### LED meanings
- 1 Hz blink (0.5s on / 0.5s off) = **Booting**
- Solid ON = **Ready** (main service is active)
- 2 blinks = **Service failed**
- 3 blinks = **Wi-Fi not connected**
- 4 blinks = **Network OK, no internet**
- 5 blinks = **Disk low**

### Setup
1. Install the updated systemd unit:
   ```sh
   sudo systemctl enable --now jv-status-led.service
   ```
2. Watch logs with:
   ```sh
   sudo journalctl -u jv-status-led.service -f
   ```

### Why this design
- A single daemon owns GPIO12 to prevent GPIO races.
- Continuous checks keep the LED accurate when Wi-Fi drops or services fail.
- systemd ordering avoids fragile boot-time sleeps.

### Assumptions
- The main app service is `magic_lid.service`.
- `iwgetid` is installed (`wireless-tools`) to detect SSID connectivity.

## Shutdown button (web UI)

**Intent:** provide a safe, user-confirmed shutdown from the web UI.

### Setup
1. Ensure the helper unit is installed:
   ```sh
   sudo systemctl status jv-poweroff.service
   ```
2. Ensure the web UI service user can start the helper:
   ```sh
   sudo test -f /etc/sudoers.d/magicbox-poweroff && echo "sudoers rule installed"
   ```
3. Use the **Shutdown** button in the web UI; confirm the prompt.

### Behavior
- The UI shows a confirmation prompt before shutdown.
- On success, the UI reports “Shutting down…” and the Pi powers off safely.
- Errors (permission, missing systemd) are returned in the UI.

### Why this design
- A dedicated oneshot systemd unit limits privileges to `systemctl poweroff`.
- The web UI only triggers the unit, avoiding broad sudo access.

### Assumptions
- systemd is available on the target OS.
- The web UI service user can call `systemctl start jv-poweroff.service` (installer writes a minimal sudoers rule).

## Managing the services

Common commands (installed with `magicbox` helper):

```sh
magicbox status        # systemctl status for both units
magicbox logs          # follow both logs
magicbox logs-main     # GPIO service logs
magicbox logs-web      # web service logs
magicbox restart       # restart both
magicbox stop|start    # stop/start both
magicbox open          # open http://localhost:<port> on this machine
```

Direct systemd equivalents:
- Status: `sudo systemctl status magic_lid.service magic_lid_web.service jv-status-led.service`
- Logs: `sudo journalctl -u magic_lid.service -u magic_lid_web.service -u jv-status-led.service -f`
- Restart: `sudo systemctl restart magic_lid.service magic_lid_web.service jv-status-led.service`

## Configuration & customization

- **Port:** set `MAGICBOX_WEB_PORT=<port>` when running `install.sh`.
- **Install location:** `MAGICBOX_TARGET=/opt/julesvern` (default) can be changed to another absolute path.
- **Service user:** `MAGICBOX_USER=<user>` to reuse an existing user (must have GPIO access); `MAGICBOX_LAUNCHER_USER=<desktop-user>` controls where the `.desktop` file is written.
- **Data directory:** `MAGICBOX_DATA_DIR=/var/lib/julesvern` (default). `MAGICBOX_STATE_DIR` may be set if you need a different state path.
- **Pin mapping:** edit `src/config.py` or use the web UI pin editor. The app respects `MAGICBOX_DATA_DIR`/`MAGICBOX_STATE_DIR` for persisted state.

## Updating

From the repo checkout (or after copying a fresh ZIP over the old files):

```sh
cd /path/to/JulesVern_MagicBox
git pull                # if using Git
sudo ./install.sh       # refresh venv, services, and launcher
```

The installer re-copies the repo into `/opt/julesvern`, keeps the service user/data directory, and reloads systemd.

## Uninstall

```sh
cd /path/to/JulesVern_MagicBox
sudo ./scripts/uninstall_pi.sh           # leaves repo and data in place
sudo PURGE_REPO=1 PURGE_DATA=1 ./scripts/uninstall_pi.sh   # also delete repo/data
sudo REMOVE_USER=1 ./scripts/uninstall_pi.sh               # additionally remove the julesvern user/home
```

This stops and disables both units, removes their unit files, deletes the helper, and removes `/etc/magicbox/config`. Data and repo are preserved unless the purge flags are set.

## Troubleshooting

- **Port already in use:** re-run `install.sh` with `MAGICBOX_WEB_PORT=<new>`.
- **GPIO permission issues:** ensure the service user is in the `gpio` group (`sudo groups julesvern`). Re-run the installer to fix membership.
- **Venv problems:** delete `/opt/julesvern/venv` (or your install path) and rerun `sudo ./install.sh`.
- **Service not starting:** check logs with `journalctl -u magic_lid.service -u magic_lid_web.service -b --no-pager` for stack traces.

## Manual run (debugging)

```sh
source /opt/julesvern/venv/bin/activate   # adjust if you changed MAGICBOX_TARGET
python /opt/julesvern/src/main.py         # GPIO service
python /opt/julesvern/src/web_server.py --port 8080
```

## Safety Notes

- Never drive LEDs without appropriate resistors.
- Verify every pin assignment (BCM vs. physical) before connecting hardware.
- Physical pin 1 supplies 3.3 V and is **not** a GPIO input—do not wire the lid switch there.
