# 05_LOGGING_AND_PERSISTENCE.md
**Jules Verne Magic Box — Logging & Persistence (Authoritative Spec)**

Logging is a **first-class output** of this system.

## Requirements (locked)
- Logs must persist across reboots
- Logs must be human-readable text
- Logs must include:
  - installer steps and failures
  - service start/stop and exceptions
  - Wi‑Fi connectivity status (detection only; no configuration)
  - web UI access/errors
  - GPIO init, input state changes (debounced), output changes
  - log export actions and failures
- Logs must be exportable to `/boot/firmware` for Windows access

## Log locations
### Primary runtime log (persistent)
- Directory: `/var/log/magicbox/`
- File: `/var/log/magicbox/magicbox.log`

### Installer log (persistent)
- Directory: `/var/log/magicbox/`
- File: `/var/log/magicbox/installer.log`

### systemd journal (supplemental)
- Service logs should also appear in `journalctl -u magicbox.service`
- The file logs above remain the canonical export source

## Rolling log policy
- Use rotation to prevent unbounded growth:
  - max size: **2 MB**
  - backups: **5**
- Rotation method can be Python logging RotatingFileHandler or equivalent.

## Export logs (I6)
Export must create a Windows-readable copy on the boot partition.

### Export destination (locked)
- Directory: `/boot/firmware/MAGICBOX_LOGS/`
- Files:
  - `magicbox.log`
  - `installer.log`
  - optional: `export_manifest.txt` (timestamp, hostname, versions)

### Export behavior
- On export request:
  1) Ensure destination directory exists
  2) Copy current log files (and optionally rotated backups)
  3) Write `export_manifest.txt`
- If export fails, set Status LED to “Log export failure” pattern during the attempt and log the failure.

## Diagnostic friendliness
- Log lines must include timestamps and log level
- Errors must include tracebacks where applicable

## No hidden logs
- Do not write logs only to tmpfs/ram
- Do not require SSH to retrieve logs (export must work)
