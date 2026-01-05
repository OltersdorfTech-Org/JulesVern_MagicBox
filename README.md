# Magic Lid GPIO Controller (Raspberry Pi Zero 2 W)

![Codex](https://img.shields.io/badge/codex-enabled-blue)
![Python](https://img.shields.io/badge/python-3.x-blue?logo=python&logoColor=white)
![Tests](https://img.shields.io/badge/tests-in%20progress-yellow)
![Version](https://img.shields.io/badge/version-unknown-lightgrey)

Headless-ready Raspberry Pi project that watches three switches (lid + two keys), drives four LEDs, and exposes a web UI for toggling the remote LID and Magic flicker flags. It targets Raspberry Pi OS **Bookworm** (Debian 12) and uses system Python packages for GPIO reliability.

> ⚠️ Confirm BCM GPIO pins before wiring (physical pin 1 is 3.3 V and **cannot** be used as a GPIO input).

## I/O Summary

| Signal       | Purpose                          | BCM GPIO | Physical Pin | Status |
|--------------|----------------------------------|----------|--------------|--------|
| LID_SWITCH   | Active-low switch to GND         | 27       | 13           | Pi Zero 2 W wiring |
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

The installer is idempotent. Re-running it refreshes services and runtime config.

> Note: Bookworm mounts the FAT boot partition at `/boot/firmware` on most systems.

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
- Copies the repo to **`/opt/julesvern/JulesVern_MagicBox`** (override with `MAGICBOX_TARGET=/some/path`).
- Uses the **existing user** who ran the installer (`$SUDO_USER` or `$USER`). No new users are created.
- Adds the runtime user to `gpio`, `adm`, and `systemd-journal` groups when present.
- Installs required packages via apt: `python3-gpiozero`, `python3-lgpio`, `python3-rpi.gpio`, `python3-flask`, and `wireless-tools`.
- Creates writable data at **`/var/lib/julesverne_magicbox`** (override with `MAGICBOX_DATA_DIR`).
- Creates writable logs at **`/var/log/julesverne_magicbox`** (override with `MAGICBOX_LOG_DIR`).
- Writes `/etc/julesverne_magicbox/runtime.conf` with `JV_USER`, `JV_REPO_DIR`, and log/data paths.
- Installs systemd units: `magic_lid.service`, `magic_lid_web.service`, `magic_lid.path`, `jv-status-led.service`, and `jv-poweroff.service`.
- Enables and starts services immediately—no manual `systemctl enable` required.
- Installs helper CLI `magicbox` and a desktop launcher for the invoking user.

## Runtime behavior

- **Autostart on boot:** both services start headlessly after networking is ready; no login or GUI needed.
- **Web UI:** available at `http://<pi-ip>:8080` by default (override during install with `MAGICBOX_WEB_PORT=<port>`).
- **Data & config:** remote state lives at `/var/lib/julesverne_magicbox/state/lid_remote_state.json`. GPIO status snapshots are written to `/var/lib/julesverne_magicbox/state/gpio_status.json`. Pin mappings and other tunables remain in `src/config.py` within `/opt/julesvern/JulesVern_MagicBox` (or your chosen install path).
- **Logging:** persistent logs are written to `/var/log/julesverne_magicbox/` and also stream to journald.
- **Config change auto-restart:** `magic_lid.path` restarts `magic_lid.service` whenever `config.py` changes.
- **Restart policy:** `Restart=always` with a 2s backoff on both units.

## Pi Ops Quickstart

### View service status
```sh
sudo systemctl status magic_lid.service --no-pager
sudo systemctl status magic_lid_web.service --no-pager
```

### View logs (journald)
```sh
sudo journalctl -u magic_lid.service -n 200 --no-pager
sudo journalctl -u magic_lid.service -f
sudo journalctl -u magic_lid_web.service -n 200 --no-pager
```

### View persistent log files
```sh
sudo tail -n 200 /var/log/julesverne_magicbox/main.log
sudo tail -n 200 /var/log/julesverne_magicbox/web.log
sudo ls -lah /var/log/julesverne_magicbox/
```

### Restart / stop / start
```sh
sudo systemctl restart magic_lid.service
sudo systemctl stop magic_lid.service
sudo systemctl start magic_lid.service
```

### Export logs to Windows-readable partition
```sh
sudo python3 tools/export_logs_to_boot.py
```
Copies the latest logs to `/boot/jv_logs/` (or `/boot/firmware/jv_logs/`) so Windows can read them.

### Health check
```sh
python3 tools/jvmb_health.py
```
Prints service state, journal tail, log tail, Wi-Fi status, internet reachability, and disk free percent.

## Web UI

The web UI provides large touch-friendly controls for safety, shutdown, GPIO configuration, and log access.

### Web log viewer

**Intent:** give headless users a quick way to read persistent logs from the SD card.  
**Setup:** start `magic_lid_web.service`, then open the web UI and expand the Logs section.  
**Why this design:** a small API returns only the latest N lines to keep the UI responsive.  
**Assumptions:** the service user can read `/var/log/julesverne_magicbox/`.

### Download logs (web)

**Intent:** provide a one-click way to download a ZIP of logs to the browser client device.  
**Setup:** open the web UI and click **Download logs** in the Logs card.  
**Why this design:** the server packages the two persistent log files plus journal tails into a single ZIP for easy support sharing.  
**Assumptions:** the service user can read `journalctl` output (typically via `adm` or `systemd-journal` group membership).

## Status LED (GPIO12)

**Intent:** expose a single external LED that tells you when the system is booting, ready, or in a fault state.

### Wiring
- **GPIO12 → resistor (330Ω–1kΩ) → LED anode**, LED cathode → **GND**.
- BCM numbering only. GPIO12 is physical pin 32.

### LED meanings
- 1 Hz blink (0.5s on / 0.5s off) = **Booting**
- Solid ON = **Ready** (main service is active)
- 2 blinks = **Main service failed**
- 3 blinks = **Web service failed**
- 4 blinks = **Wi-Fi not connected**
- 5 blinks = **Network OK, no internet**
- 6 blinks = **Disk low**

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
- The web UI service is `magic_lid_web.service`.
- `iwgetid` is installed (`wireless-tools`) to detect SSID connectivity.
- Disk warnings appear before network warnings when multiple issues occur.

## Persistent logging & export

**Intent:** store log files on the SD card and make them easy to read on Windows.  
**Setup:** logs write automatically to `/var/log/julesverne_magicbox/`; run `magicbox export-logs` (or `python3 tools/export_logs_to_boot.py`) to copy them to `/boot/jv_logs/` (or `/boot/firmware/jv_logs/`).  
**Why this design:** log rotation keeps SD card usage bounded while the export step provides a FAT-readable copy.  
**Assumptions:** the SD card boot partition is mounted at `/boot` or `/boot/firmware`.

## Health check tool

**Intent:** provide a single command that summarizes service state, logs, Wi-Fi, internet reachability, and disk space.  
**Setup:** run `python3 tools/jvmb_health.py` from the repo checkout.  
**Why this design:** keeps the health check simple and scriptable without extra dependencies.  
**Assumptions:** `systemctl` and `journalctl` are available on the target OS.

## GPIO self-test tool

**Intent:** verify LEDs and switches without starting the full GUI.  
**Setup:** run `python3 tools/gpio_selftest.py` (add `--monitor` to watch inputs for 10 seconds).  
**Why this design:** a small CLI loop avoids relying on the web UI for hardware testing.  
**Assumptions:** GPIO wiring matches `src/config.py` and the user has GPIO permissions.

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
```

## Notes

- Group membership changes may require a reboot or re-login before GPIO access works.
- If `/var/log/julesverne_magicbox` is not writable, the services fall back to a log folder in the service user's home directory.
