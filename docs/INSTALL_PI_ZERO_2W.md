# Install Magic Box on Raspberry Pi Zero 2 W (Bookworm)

This guide covers the two supported workflows with explicit, copy/pasteable commands. No Git is required on the Pi.

- **Windows SD Card Method (no Git):** copy the repo to the SD card, boot, run one command.
- **Pi Method (one command from the repo):** run the installer directly from the checkout.

All steps assume Raspberry Pi OS Bookworm on a Pi Zero 2 W.

## 1) Windows SD Card Method (No Git)
1. On your Windows PC, download the repository ZIP from GitHub and extract it.
2. Insert the Raspberry Pi SD card. The small FAT partition mounts in File Explorer (commonly the `boot`/`firmware` drive). If it is not visible, assign a drive letter in **Disk Management**.
3. Copy the entire `JulesVern_MagicBox` folder to the root of the boot/firmware drive. Ensure the folder contains `sdcard_bootstrap/install.sh`.
4. Safely eject the SD card and boot the Pi.
5. On the Pi, open **Terminal** and run exactly one command:
   ```sh
   sudo /boot/firmware/JulesVern_MagicBox/sdcard_bootstrap/install.sh
   ```
   The script copies the repo to `/home/pi/JulesVern_MagicBox` (override with `MAGICBOX_TARGET=/some/path` if needed), sets up the virtual environment, installs dependencies, writes the systemd units, and starts the GPIO service.
6. Wait for the final `SUCCESS` message. You can now use the `magicbox` helper (see below).

## 2) Pi Method (One Command from the Repo)
If the repo is already on the Pi (copied via USB, SCP, or the SD method above), run the installer directly:
```sh
cd /home/pi/JulesVern_MagicBox  # adjust if your path differs
sudo ./INSTALL_MAGIC_BOX.sh
```
This is idempotent; re-running it refreshes dependencies and systemd units.

## Helper command (installed automatically)
After installation, control everything with the `magicbox` command:
```sh
magicbox status   # show service status
magicbox start    # start the GPIO service
magicbox stop     # stop the GPIO service
magicbox restart  # restart the GPIO service
magicbox logs     # follow logs
magicbox install  # re-run the installer with the saved path/user
```

## Systemd details
- Main service: `magic_lid.service` (enabled by default)
- Optional web UI: `magic_lid_web.service` (installed but **not** enabled; enable with `sudo systemctl enable --now magic_lid_web.service`)
- Logs: `journalctl -u magic_lid.service -f` (or `magicbox logs`)
- Status: `sudo systemctl status magic_lid.service` (or `magicbox status`)
- Start/stop manually: `sudo systemctl start|stop|restart magic_lid.service`
- Disable autostart: `sudo systemctl disable magic_lid.service`

## Common failure modes and fixes
- **Installer says it must run as root:** prefix the command with `sudo`.
- **Repo not found / wrong path:** ensure `JulesVern_MagicBox` is present at `/boot/firmware` for the SD method or adjust the path in the command. If the `magicbox` helper complains, edit `/etc/magicbox/config` to point `REPO_DIR` to your checkout, then re-run `magicbox install`.
- **Missing Python venv module:** the installer installs `python3-venv` via apt automatically; re-run the installer if interrupted.
- **User mismatch:** services run as `${SUDO_USER}` by default (usually `pi`). To force a user, run the installer with `MAGICBOX_USER=<user>` exported in the command.
- **Services fail to start after moving the repo:** update `/etc/magicbox/config` with the new `REPO_DIR` and run `magicbox install` to refresh systemd unit paths.

## What the installer does
- Verifies Linux/Pi hardware and exits if not root.
- Installs apt prerequisites (`python3-venv`, GPIO libraries).
- Creates or refreshes a Python virtual environment at `<repo>/.venv` and installs `requirements.txt`.
- Writes systemd units pointing at the repo and virtualenv, enables `magic_lid.service`, and installs a `/usr/local/bin/magicbox` helper.
- Stores config in `/etc/magicbox/config` for repeat installs.

## Design notes & assumptions
- Uses systemd (not cron) for reliable boot-time start on Bookworm.
- Runs services as the invoking sudo user (`pi` by default) so GPIO access aligns with Pi defaults.
- Keeps all assets text-only for SD card compatibility; no Git is required on the Pi.
- The web service is optional to reduce boot overhead on the Pi Zero 2 W; enable only if needed.
