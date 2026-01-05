# Install Magic Box on Raspberry Pi Zero 2 W (Bookworm)

This guide covers the supported workflow with explicit, copy/pasteable commands. No Git is required on the Pi.

All steps assume Raspberry Pi OS Bookworm on a Pi Zero 2 W.

## Install from a local checkout (one command)
If the repo is already on the Pi (copied via USB, SCP, or `rsync`), run the installer directly:
```sh
cd /home/pi/JulesVern_MagicBox  # adjust if your path differs
sudo ./install.sh
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
magicbox export-logs  # export logs to boot partition for Windows access
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
- **Repo not found / wrong path:** ensure `JulesVern_MagicBox` is present at the path you `cd` into. If the `magicbox` helper complains, edit `/etc/julesverne_magicbox/runtime.conf` to point `JV_REPO_DIR` to your checkout, then re-run `magicbox install`.
- **User mismatch:** services run as `${SUDO_USER}` by default (usually `pi`). To force a user, run the installer with `MAGICBOX_USER=<user>` exported in the command.
- **Services fail to start after moving the repo:** update `/etc/julesverne_magicbox/runtime.conf` with the new `JV_REPO_DIR` and run `magicbox install` to refresh systemd unit paths.

## What the installer does
- Verifies Linux/Pi hardware and exits if not root.
- Installs apt prerequisites (`python3`, GPIO libraries).
- Writes systemd units pointing at the repo, enables `magic_lid.service`, and installs a `/usr/local/bin/magicbox` helper.
- Stores config in `/etc/julesverne_magicbox/runtime.conf` for repeat installs.

## Design notes & assumptions
- Uses systemd (not cron) for reliable boot-time start on Bookworm.
- Runs services as the invoking sudo user (`pi` by default) so GPIO access aligns with Pi defaults.
- Keeps all assets text-only for SD card compatibility; no Git is required on the Pi.
- The web service is optional to reduce boot overhead on the Pi Zero 2 W; enable only if needed.
