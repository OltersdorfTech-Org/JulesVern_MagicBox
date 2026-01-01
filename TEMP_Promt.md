# CODEX PROMPT — JulesVern_MagicBox (Raspberry Pi) Logging + Service Boot Fix + GPIO Noise + LED Status Codes + Web Log Viewer

Repo: https://github.com/OltersdorfTech-Org/JulesVern_MagicBox

You are Codex acting as a senior Raspberry Pi + Python reliability engineer. Make changes directly in the repo with clean commits and update docs. Do NOT add an installer; this is a Pi app. Assume headless operation is common.

## Problem recap (from physical Pi testing)
- Status LED on GPIO12 starts, but shows 2-blink “service failed” (main service not reliably starting on boot).
- No logs are being stored persistently.
- User doesn’t know how to view logs on a running headless system.
- Running `Main.py` manually spams `KEY2 pressed/released` repeatedly with **no physical GPIO connection** (likely floating input / missing pull-up/down / bounce).
- When external LEDs or multimeter connected, no state changes observed when switches triggered (aside from GPIO12 status LED).
- Need logging that is **stored on SD card**, accessible by a Windows machine (not in RAM).
- README must document clear commands to check status, view logs, start/stop/restart services.
- Update LED meaning table to specific codes below.
- Web GUI: add a **show/hide logs** section at the very bottom that streams/loads logs from disk.

## High-level goals
1) Make the main service start reliably on boot (systemd).
2) Implement robust, persistent logging to SD card (rotating logs), plus journald integration.
3) Fix GPIO input noise/floating behavior that produces phantom KEY2 events.
4) Ensure switch->LED behaviors actually toggle GPIO outputs (and document pin mapping).
5) Implement new status LED blink codes on GPIO12:
   - 1 Hz blink (0.5s on / 0.5s off) = Booting
   - Solid ON = Ready (main service active)
   - 2 blinks = Main Service failed
   - 3 blinks = Web Service Failed
   - 4 blinks = Wi-Fi not connected
   - 5 blinks = Network OK, no internet
   - 6 blinks = Disk low
6) Web GUI: bottom section with “Show logs” toggle; view latest N lines; optionally auto-refresh.
7) README: copy-pasteable Pi commands for logs + service control + health checks.

---

# Implementation requirements

## A) Logging (persistent, SD-card, Windows accessible)
- Create a single canonical log directory on the Pi that is on the SD card:
  - Prefer: `/var/log/julesverne_magicbox/`
  - Ensure it is created on install/first run and writable by the service user.
- Use Python `logging` with `RotatingFileHandler` (or TimedRotatingFileHandler) so logs never grow unbounded.
  - Example files:
    - `/var/log/julesverne_magicbox/main.log`
    - `/var/log/julesverne_magicbox/web.log`
    - `/var/log/julesverne_magicbox/gpio.log` (optional; can also be merged into main)
- Logs MUST be plain text and readable when SD card is mounted on Windows (ext4 isn’t natively readable on Windows; so also provide **a “copy logs to FAT/boot partition” helper**):
  - Implement a CLI command or script that copies the latest logs to `/boot/jv_logs/` (or `/boot/firmware/jv_logs/` depending on Pi OS) so a Windows machine can read them without ext4 support.
  - The script should create the destination directory if missing.
  - Name it something like: `tools/export_logs_to_boot.py` and document usage in README.
- Also ensure the systemd service logs are visible via journald:
  - StandardOutput=journal
  - StandardError=journal
- Add a small “startup banner” log line including git commit hash (if available), hostname, IP(s), disk free %, and app version.

## B) systemd service reliability
- Inspect existing systemd unit(s) in the repo. Fix them so the service starts after network is usable and the filesystem is ready.
- Requirements for the **main** service unit:
  - `Restart=on-failure` with a sensible backoff (RestartSec=2 or 5)
  - `WorkingDirectory` set correctly
  - Use absolute paths to python and to the main entrypoint
  - Ensure it runs as a non-root user unless GPIO library requires root; if root is required, document it and keep scope minimal.
  - Add `Environment=PYTHONUNBUFFERED=1`
  - If the web service is separate, ensure it has its own unit and dependency chain.
- Add a `jvmb-health` command (simple script) that prints:
  - service status (systemctl is-active)
  - last 20 journal lines
  - last 20 lines of main.log
  - wifi status + IP
  - internet reachability (ping 1.1.1.1 and/or DNS)
  - disk free %
- Document service names in README and keep them consistent.

## C) Fix floating GPIO inputs / phantom KEY2
- Find the GPIO input handling for KEY2 (and other keys).
- Implement BOTH software and hardware-safe defaults:
  1) In code: configure inputs with explicit pull-up or pull-down resistors via the GPIO library:
     - For RPi.GPIO: `GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)` (or PUD_DOWN)
     - For gpiozero: use `Button(pin, pull_up=True, bounce_time=...)`
  2) Add debounce:
     - For interrupts: `bouncetime=50` to `200` ms depending on switch
     - For polling: implement stable-state detection (e.g., require N consistent reads over M ms)
- If KEY2 is truly analog in the design, but is being read as digital, correct the design:
  - If there is no ADC hardware, do NOT treat it as analog.
  - If the pin is unused/optional, disable it by default and require enabling in config.
- Ensure with **nothing connected** to KEY2 pin, it does not spam events.
- Add a debug log for key state transitions with rate limiting (don’t flood logs).

## D) Ensure LED/switch IO actually changes state
- Locate the outputs for the “other LEDs” (not the status LED).
- Ensure outputs are configured as outputs and set high/low properly.
- Confirm pin numbering scheme (BCM vs BOARD) is consistent everywhere.
- Add a single config file (or constants module) defining all GPIO pins and whether they are active-high/active-low.
- Add a CLI test tool: `tools/gpio_selftest.py` that:
  - blinks each output LED in sequence
  - prints the input states
  - optionally runs an input monitor for 10 seconds
- This tool must be safe and not require the full GUI to run.

## E) Status LED patterns on GPIO12
- Implement a robust status LED controller that:
  - runs in its own thread/task
  - can be updated at runtime (booting -> ready -> error codes)
  - avoids blocking the main thread
- Behavior:
  - Booting: 1 Hz blink (0.5s on / 0.5s off)
  - Ready: solid on
  - Errors: blink N times, pause, repeat (e.g. blink-blink … pause 1.5s … repeat)
- Define error states:
  - 2 = Main Service failed
  - 3 = Web Service Failed
  - 4 = Wi-Fi not connected
  - 5 = Network OK, no internet
  - 6 = Disk low
- Implement checks:
  - Wi-Fi connected: check `iwgetid -r` or `nmcli -t -f ACTIVE,SSID dev wifi` depending on availability; handle missing commands gracefully.
  - Internet: ping 1.1.1.1 OR attempt DNS resolve + HTTP HEAD to a stable endpoint; keep timeouts short.
  - Disk low: threshold configurable (default warn < 10% free or < 1GB free). Use `shutil.disk_usage`.
- Priority rules:
  - If main service is running normally: show Ready (solid on) unless a higher-priority warning should override (disk low, no internet, etc.). Decide a clear priority order and document it.
  - If web service is down but main is up: show 3 blinks.
  - If main is down: show 2 blinks.

## F) Web GUI: show/hide logs at bottom
- Identify the web app framework (Flask/FastAPI/etc.).
- Add a collapsible section at the very bottom:
  - Button: “Show logs” / “Hide logs”
  - When shown:
    - Dropdown: main.log / web.log
    - Text area: last N lines (default 200)
    - Optional auto-refresh every 2 seconds (toggle)
- Logs must be read from the SD-card log directory.
- Ensure log read is safe:
  - no huge file reads
  - handle file missing
  - sanitize output (escape HTML)
- Add a small endpoint like `/api/logs?file=main&lines=200` returning JSON.

## G) README updates (must be concrete and copy/pasteable)
Update README with a “Pi Ops Quickstart” section including:

### View service status
- `sudo systemctl status <MAIN_SERVICE_NAME> --no-pager`
- `sudo systemctl status <WEB_SERVICE_NAME> --no-pager` (if exists)

### View logs (journald)
- `sudo journalctl -u <MAIN_SERVICE_NAME> -n 200 --no-pager`
- `sudo journalctl -u <MAIN_SERVICE_NAME> -f`
- Same for web service

### View persistent log files
- `sudo tail -n 200 /var/log/julesverne_magicbox/main.log`
- `sudo tail -n 200 /var/log/julesverne_magicbox/web.log`
- `sudo ls -lah /var/log/julesverne_magicbox/`

### Restart / stop / start
- `sudo systemctl restart <MAIN_SERVICE_NAME>`
- `sudo systemctl stop <MAIN_SERVICE_NAME>`
- `sudo systemctl start <MAIN_SERVICE_NAME>`

### Export logs to Windows-readable partition
- `sudo python3 tools/export_logs_to_boot.py`
- Mention where it copies to (e.g. `/boot/jv_logs/`) and that Windows can read those files.

### Health check
- `python3 tools/jvmb_health.py` (or similar) and what it prints.

### LED status meanings
Include the exact mapping:
- 1 Hz blink (0.5s on / 0.5s off) = Booting
- Solid ON = Ready (main service is active)
- 2 blinks = Main Service failed
- 3 blinks = Web Service Failed
- 4 blinks = Wi-Fi not connected
- 5 blinks = Network OK, no internet
- 6 blinks = Disk low

Also add a “GPIO troubleshooting” note:
- Explain floating inputs + need for pull-up/down.
- State which pins use internal pull-ups and expected wiring.

---

# Constraints
- Prefer standard library + minimal dependencies.
- Keep code clean and testable; add unit tests where reasonable (e.g., for status decision logic, log export path selection).
- Don’t break current functionality: app should still run manually with `python3 Main.py` (or documented entrypoint).
- If multiple entrypoints exist (Main.py, web server), unify into a clear structure but do not do a massive rewrite unless necessary.

---

# Deliverables (must be included in PR)
1) Code changes implementing A–F.
2) Updated systemd unit files (or installer docs if units are generated).
3) New tools:
   - `tools/export_logs_to_boot.py`
   - `tools/gpio_selftest.py`
   - `tools/jvmb_health.py`
4) Updated README with the exact command lines and LED mapping above.
5) A brief CHANGELOG entry (or release notes section) summarizing the fix.

---

# Acceptance tests (you must validate logically and via code)
- With no GPIO wiring connected: no repeated KEY2 pressed/released spam.
- After boot, main service becomes active and status LED goes solid ON.
- If main service fails to start: status LED shows 2 blinks repeating; `journalctl` shows error; persistent log file exists.
- Logs are written to `/var/log/julesverne_magicbox/` and rotate correctly.
- Running `tools/export_logs_to_boot.py` creates `/boot/jv_logs/` (or `/boot/firmware/jv_logs/`) and copies recent logs.
- Web GUI shows logs in the new bottom toggle section and can fetch last N lines without freezing.

Proceed to implement now.
