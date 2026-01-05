# CODEX AGENT PROMPT — JulesVern_MagicBox repo refactor + Bookworm-stable GPIO + logging/export + README cleanup

You are a code-modifying agent working on this repository:
https://github.com/OltersdorfTech-Org/JulesVern_MagicBox

## Context / problems to fix (from real device logs)
- `magic_lid.service` fails at boot and/or is in an error state.
- GPIO initialization fails with gpiozero backends missing (`No module named 'lgpio'`, `No module named 'RPi'`, `No module named 'pigpio'`) and then `OSError: [Errno 22] Invalid argument` when it falls back to deprecated sysfs export.
- Logs are not reliably persisted to the SD card and not exported to the Windows-readable FAT boot partition.
- Repo has duplication / drift (multiple installer scripts, outdated files). Needs refactor: remove old files, consolidate install flow, simplify, update README with clean commands.
- Must target Raspberry Pi OS **Bookworm** (Debian 12), timeframe ~ Nov 2025.
  - Bookworm mounts the FAT boot partition at `/boot/firmware` (not `/boot`). (Confirm in your research + implement robust detection.)
  - Default Python is typically 3.11.x; avoid relying on Python 3.13 for GPIO compatibility.
- Must NOT create new users. Use the *existing* user that runs the installer, and elevate via sudo when needed.
- GPIO service must automatically start on boot, and pin updates via `config.py` must take effect post-boot (via restart trigger or safe reload).
- Web GUI must include an option to download logs to the *client device* (the browser user) as a file.

## High-level approach (research + confirm best practice before changing code)
1. Inspect the repo structure and current install/service/logging approach.
2. Identify duplicates (especially install.sh or older variants), deprecated folders, unused scripts. Produce a plan, then implement:
   - Consolidate to ONE installer entrypoint (e.g., `install.sh`), and remove/archived duplicates.
   - Standardize paths and naming (services, log dir, tools).
3. Fix GPIO backend availability on Bookworm:
   - Ensure installer uses apt (not pip) to install: `python3-gpiozero`, `python3-lgpio`, and `python3-rpi.gpio` (and any other required OS packages).
   - Ensure the runtime uses system python (`/usr/bin/python3`) unless you can prove a venv is safe *and* includes system site packages (`--system-site-packages`). GPIO backends are often OS-packaged.
4. Logging:
   - Ensure persistent logs stored on ext4 in `/var/log/julesverne_magicbox/` (or similarly named, choose one and standardize).
   - Ensure log directory permissions are correct for the service user.
   - Keep journald logging available too (do not disable).
5. Export logs to FAT boot partition so Windows can read:
   - Robustly detect `/boot/firmware` vs `/boot`.
   - Copy latest logs to `/boot/firmware/jv_logs/` (or `/boot/jv_logs/` fallback).
   - Provide a tool script `tools/export_logs_to_boot.py` and document it.
   - Must handle permissions (FAT mount is typically root-owned); script should be run with sudo.
6. Service reliability:
   - Provide/repair `magic_lid.service` and `magic_lid_web.service`.
   - Must start at boot, auto-restart on crash.
   - Must run as the existing user (installer user). Do not create a special service user.
   - Ensure the service can access GPIO by adding installer user to `gpio` group.
7. Pins update post-boot:
   - Implement a systemd `.path` unit (preferred) that restarts `magic_lid.service` when `config.py` changes; OR implement safe config reload in code. Choose the most robust + simplest.
8. Web GUI log download to client device:
   - Add an endpoint that returns a ZIP (or tar.gz) of logs and optionally recent journal tail.
   - Add a simple “Download Logs” button in the UI to fetch that file.

## Concrete tasks (do these in-repo)

### A) Repository refactor / dedup
- Identify duplicate install scripts and any obsolete files.
- Delete or move old/unused scripts in a clearly labeled folder (e.g., `deprecated/`), or remove entirely if safe.
- Make ONE canonical installer: `install.sh` (or `scripts/install.sh`) — pick one location, update README accordingly.
- Ensure the repo structure is clean:
  - `tools/` for utilities like export and health check
  - `services/` or `systemd/` for unit files
  - `web/` or `ui/` for the web GUI assets
  - avoid multiple copies of the same file with minor changes

### B) Installer (Bookworm-safe; no assumptions)
Installer must:
- `sudo apt update`
- install required apt packages (at minimum):
  - `python3-gpiozero`
  - `python3-lgpio`
  - `python3-rpi.gpio`
  - plus any required for the web service (flask/fastapi/etc) using apt if available; otherwise use venv **with** `--system-site-packages` so it can see apt-provided gpio libs.
- add the installer-running user (call it `$SUDO_USER` if present, else `$USER`) to groups:
  - `gpio`, and optionally `adm` so it can read logs; do not assume group exists—check and handle.
- install/enable systemd units:
  - `magic_lid.service`
  - `magic_lid_web.service`
  - `magic_lid.path` (if you choose path-trigger restart)
- create log dir:
  - `/var/log/julesverne_magicbox/`
  - set ownership to the runtime user and group `adm` (or appropriate), mode 775
- print post-install instructions, including “reboot recommended to apply group membership”

### C) Systemd units
Provide/repair unit files with these requirements:
- Run as the existing user (the one who installed), not root.
  - Implement by writing a config file at install time (e.g., `/etc/julesverne_magicbox/runtime.conf`) containing `JV_USER=...`, then `EnvironmentFile=` in the unit, and `User=${JV_USER}`.
- Use `/usr/bin/python3` for GPIO service unless you can justify venv approach.
- `WorkingDirectory` set to repo install location (determine; likely `/opt/julesvern/JulesVern_MagicBox`).
- `Restart=always`, `RestartSec=2`
- Ensure services can read `config.py`.
- For logging: either let journald capture stdout/stderr AND app writes its own file logs. Do not rely solely on `StandardOutput=append:` because file ownership can be tricky.

### D) Python logging (persistent)
In `Main.py` and the web service entrypoint:
- Use Python `logging` with `RotatingFileHandler` writing to:
  - `/var/log/julesverne_magicbox/main.log`
  - `/var/log/julesverne_magicbox/web.log`
- Include timestamps, level, module, line number.
- Ensure errors go to `*.err.log` OR include ERROR-level in same file; pick a consistent scheme.
- Make sure the log dir exists; if not, fall back to user home dir with a warning (but installer should create it).

### E) Tools
Add these tools (or refactor existing ones):
1) `tools/export_logs_to_boot.py`
   - When run with sudo, it copies latest persistent logs to:
     - `/boot/firmware/jv_logs/` if `/boot/firmware` is a mountpoint
     - else `/boot/jv_logs/`
   - Copies `main.log`, `web.log`, and optionally `*.err.log`, plus a `LAST_EXPORT.txt` timestamp.
   - Must not crash if logs missing.
2) `tools/jvmb_health.py`
   - Prints:
     - systemd service status for `magic_lid.service` and `magic_lid_web.service`
     - last 100-200 lines of journal for each service
     - tail of persistent logs
     - wifi status (basic), internet reachability (ping or curl), disk free %
   - Must run without needing additional packages beyond what installer provides.
   - If run without sudo, degrade gracefully (print what it can).

### F) GPIO backend + compatibility
- Ensure gpiozero uses a real backend on Bookworm:
  - Prefer lgpio or RPi.GPIO.
  - Avoid sysfs export fallback.
- Add a short runtime self-check in `Main.py` startup:
  - Log which pin factory is in use (gpiozero can reveal this).
  - If no usable backend, log a clear fatal message and exit.

### G) Config pin changes post-boot
- Implement systemd path unit:
  - `magic_lid.path` watches the actual config file path and triggers restart of `magic_lid.service` on modification.
- Document it and ensure it’s enabled.

### H) Web GUI: download logs to client device
- Add a backend endpoint:
  - `GET /api/logs/download` → returns a ZIP containing:
    - `/var/log/julesverne_magicbox/main.log`
    - `/var/log/julesverne_magicbox/web.log`
    - optionally `journalctl -u magic_lid.service -n 200` output as `journal_magic_lid.txt`
    - optionally `journalctl -u magic_lid_web.service -n 200` output as `journal_magic_lid_web.txt`
- Frontend:
  - Add a “Download Logs” button that triggers browser download.
- Security:
  - If the web UI is intended for LAN only, keep it simple; otherwise add minimal protection (at least optional basic auth or “local only” binding). Decide based on existing repo patterns.

## README rewrite (clean + practical)
Rewrite README so it is:
- minimal, correct, Bookworm-targeted
- includes install steps and what it installs (do not assume anything is present)
- includes the helpful command snippets exactly like these (update paths if needed):

Service status:
sudo systemctl status magic_lid.service --no-pager
sudo systemctl status magic_lid_web.service --no-pager

View logs (journald):
sudo journalctl -u magic_lid.service -n 200 --no-pager
sudo journalctl -u magic_lid.service -f
sudo journalctl -u magic_lid_web.service -n 200 --no-pager

View persistent log files:
sudo tail -n 200 /var/log/julesverne_magicbox/main.log
sudo tail -n 200 /var/log/julesverne_magicbox/web.log
sudo ls -lah /var/log/julesverne_magicbox/

Restart / stop / start:
sudo systemctl restart magic_lid.service
sudo systemctl stop magic_lid.service
sudo systemctl start magic_lid.service

Export logs to Windows-readable partition:
sudo python3 tools/export_logs_to_boot.py
Copies the latest logs to /boot/jv_logs/ (or /boot/firmware/jv_logs/) so Windows can read them.

Health check:
python3 tools/jvmb_health.py
Prints service state, journal tail, log tail, Wi-Fi status, internet reachability, and disk free percent.

Also add:
- Note that Bookworm boot partition is typically `/boot/firmware`.
- Note that group membership changes may require reboot or re-login.
- Note where to edit pins in `config.py` and that it auto-restarts on changes (via `.path` unit).

## Acceptance criteria (must be true)
- After running installer and rebooting, `magic_lid.service` and `magic_lid_web.service` are `active (running)`.
- GPIO initializes without falling back to sysfs export; logs show a valid backend (lgpio or RPi.GPIO).
- Logs persist to `/var/log/julesverne_magicbox/`.
- `sudo python3 tools/export_logs_to_boot.py` creates `/boot/firmware/jv_logs/` (or `/boot/jv_logs/`) and copies logs there.
- Editing `config.py` triggers service restart (and new pins take effect).
- Web UI has a “Download Logs” button that downloads a zip to the client device.

## Deliverables (commit-ready)
- Cleaned repo structure, duplicates removed.
- Updated installer script.
- Updated/added systemd unit files (+ optional path unit).
- Tools added/updated (`export_logs_to_boot.py`, `jvmb_health.py`).
- Web UI endpoint + button for downloading logs.
- Updated README.
- Ensure everything is referenced correctly from the install location used by the repo.

Proceed to implement all changes directly in the repo with clean commits and clear messages.
