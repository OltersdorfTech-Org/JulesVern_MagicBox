You are modifying this repo: https://github.com/OltersdorfTech-Org/JulesVern_MagicBox

Follow AGENTS.md conventions for structure, testing, logging, and changes. Do NOT harden security; this device is intended for trusted LAN use and should prioritize debuggability and “just works.”

## Problem report (from physical Raspberry Pi Zero 2 W test)

Physical wiring used in test:
- GPIO12 -> Red LED -> 330Ω -> GND  (Status LED)
- GPIO04 -> White LED -> 150Ω -> GND (Lid light LED)
- GPIO27 -> Lid switch -> GND (active-low)

Observed behavior:
- Immediately on power, GPIO04 lid LED is dimly illuminated solid (before app fully boots).
- During boot, GPIO12 blinks “booting” as expected, then goes solid “ready” for ~5 seconds.
- Web service is running and connectable.
- Then GPIO12 changes to repeated 2-blink error pattern.
- GPIO04 lid LED never changes (stays dim).
- Lid switch has no effect; web GUI shows unknown lid switch state.
- Restarting `sudo systemctl restart magic_lid.service` reproduces the same results.

Logging/export issues:
- Logs are now visible on-device, but are NOT exportable to boot folder for easy reading on Windows / importing into Codex.
- Running `sudo python3 tools/export_logs_to_boot.py` gives a path/file-not-found error.
- Manual copy from `/var/log/julesverne_magicbox/` to `/boot/firmware/jv_logs` hits permissions errors.

Installer requirement:
- Installer must set/grant FULL practical permissions for the normal user and/or provide a frictionless export mechanism.
- This device is NOT intended to be hardened. Prefer usability and diagnostics.

## Primary goals

A) Make GPIO behavior correct with the provided wiring:
- GPIO4 must be configured as a proper output and should default to OFF (LOW) immediately at service start.
- GPIO27 lid switch must be read reliably (active-low with pull-up enabled) and reflected in both:
  1) the GPIO service behavior
  2) the web UI state display
- GPIO12 status LED patterns must correspond to real fault states and be backed by a clear log message.

B) Fix the “unknown lid switch state” in the web UI:
- The web UI must display a definite state (OPEN/CLOSED or HIGH/LOW) once the GPIO service is up.
- If the GPIO service is down/unavailable, show an explicit error (not “unknown”) and include the last error message.

C) Fix log exporting so Windows can read logs from the boot partition:
- Provide a robust export script and a CLI entry point (e.g., `magicbox export-logs`) that:
  - Works no matter the current working directory.
  - Collects logs from journald for both services (magic_lid.service and magic_lid_web.service) AND any app log files if present.
  - Writes them into a boot-partition folder that exists and is predictable:
    - Prefer `/boot/firmware/jv_logs/` (Bookworm), but auto-fallback to `/boot/jv_logs/` if `/boot/firmware` is not present.
  - Creates a timestamped subfolder: `jv_logs/YYYY-MM-DD_HHMMSS/`
  - Writes:
    - `magic_lid.service.log` (journalctl output)
    - `magic_lid_web.service.log` (journalctl output)
    - `system_info.txt` (uname, OS release, python version, pip freeze, ip addr)
    - `config_snapshot.json/txt` (current pin mapping + key settings)
    - `state_snapshot.json` (remote state file if used)
  - Ends by printing the exact export path and how to copy it off from Windows.

D) Fix installer permissions so exports and logs don’t get blocked:
- Ensure the runtime user has practical read access to logs and state.
- Ensure the export script works when run via sudo and also works when run as the normal user IF possible.
- If boot partition permissions are the blocker (vfat mount behavior), ensure the export tool can still complete by:
  - Running the final write step via sudo OR
  - Writing into a location that is guaranteed writable, then copying into boot via sudo.
- Prefer “it works” over perfect POSIX purity.

## Implementation details / expected changes

1) Pin mapping + early initialization
- Locate the pin configuration (likely `src/config.py` or equivalent).
- Update defaults to match the test wiring:
  - STATUS_LED = GPIO12
  - LID_LED = GPIO4
  - LID_SWITCH = GPIO27
- Ensure LEDs are initialized as outputs with initial OFF state immediately.
  - If using gpiozero, use LED(..., initial_value=False) where available.
  - If using RPi.GPIO, set mode and output LOW before any other logic.
- Ensure the lid switch uses pull-up and is debounced (software debounce ~20–50ms).
- If the service crashes during init, log the exception and blink the 2-blink pattern (or define a clearer pattern map).

2) Service error clarity
- Wherever the status LED 2-blink pattern is triggered, also log:
  - the exception stack trace
  - a short “fault reason” string
- Add a “health” endpoint or status file that the web UI can read to show:
  - whether GPIO service is running
  - last read of lid switch
  - last error (if any)

3) Web UI “unknown lid switch state”
- Ensure web UI reads from the same source as the GPIO controller (shared module / IPC / state file).
- If the GPIO service is the authority, expose state via:
  - a local file in `/var/lib/julesvern/state/` OR
  - localhost HTTP endpoint OR
  - Unix socket
  Choose simplest that matches existing architecture.
- Replace “unknown” with:
  - “OPEN” / “CLOSED” if valid
  - “GPIO SERVICE DOWN: <reason>” if invalid/unavailable

4) Log export tooling
- Fix `tools/export_logs_to_boot.py` so it:
  - Uses absolute paths based on `__file__` and repo root detection.
  - Never assumes a working directory.
  - Autodetects boot mount path: `/boot/firmware` else `/boot`.
  - Creates `jv_logs` and a timestamp subfolder.
  - Uses `journalctl` to dump logs for both services.
  - Captures system info snapshots.
- Add command to helper CLI (`magicbox`) if present:
  - `magicbox export-logs` -> runs the exporter and prints the final path.

5) Installer changes
- In install scripts (install.sh and sdcard_bootstrap install if relevant):
  - Ensure required directories exist:
    - `/var/lib/julesvern/...`
    - optional `/var/log/julesverne_magicbox/...` if the project uses file logs
    - `/boot/firmware/jv_logs` (or create on first export)
  - Ensure ownership/permissions are practical:
    - Give the launcher user and/or `julesvern` user read/write as needed.
    - If using a dedicated service user, add the invoking user (pi) to the same group.
    - Prefer group-writable dirs and/or ACLs; if simplest, allow broad write for logs/export dirs.
- Update README with:
  - The confirmed wiring table matching GPIO12/GPIO4/GPIO27.
  - A short “Export logs to Windows” section with one command.

## Tests / validation

Add or update tests to cover:
- Config mapping loads correct pins.
- Lid switch logic inverts correctly (active-low).
- LED outputs default OFF at startup.
- Export script path resolution works from any working directory (unit test or integration-style test with temp dirs).
- Web UI state display uses real state / shows meaningful errors.

## Acceptance criteria

- With the stated wiring, lid LED is OFF by default after service starts, and can be toggled by the system logic.
- Lid switch state is correctly reported in web UI (no “unknown” when GPIO service is healthy).
- GPIO12 error blinks correspond to real errors and the reason is visible in logs.
- `magicbox export-logs` or `python3 tools/export_logs_to_boot.py` produces a readable folder on boot partition with journald logs and system snapshot, without path-not-found errors.
- README includes the one-liner to export logs and the updated wiring table.

Proceed with implementation across the repo. Keep changes minimal but robust. Document any new config keys.
