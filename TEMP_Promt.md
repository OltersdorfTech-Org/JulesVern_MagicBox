# GPT-Codex Prompt — JulesVern_MagicBox: GPIO12 Status LED + Fault Blink Patterns + GUI Shutdown Button

Repo: https://github.com/OltersdorfTech-Org/JulesVern_MagicBox  
Target hardware: Raspberry Pi Zero 2 W (headless), Raspberry Pi OS (Lite OK)  
GPIO status LED pin: **BCM GPIO 12**

## Objective
1) Add a single external **status LED** driven by **BCM GPIO 12** with:
- BOOTING indication
- READY (solid on) when the main app is truly running
- Fault blink patterns for common failures (Wi-Fi, service crash, “etc”)

2) Add a **Shutdown** button in the existing GUI that triggers a **safe Pi shutdown** (no yanking power).

Deliverables must be committed to the repo:
- Python module(s) for LED control + fault monitoring
- systemd unit file(s) to wire LED state to service lifecycle (no sleeps)
- GUI changes + backend endpoint/handler for shutdown
- README/docs updates

No installers. No GUI dependencies beyond what the repo already uses. No blocking boot.

---

## Part A — Status LED (GPIO12)

### Hardware
- LED + series resistor (330Ω–1kΩ) wired: **GPIO12 → resistor → LED anode**, LED cathode → **GND**
- GPIO is 3.3V. Keep current modest.

### LED states (exact patterns)
Use these patterns exactly (single LED):

1) **BOOTING**
- Pattern: `1 Hz` blink = 0.5s ON / 0.5s OFF (loop)
- Active at boot until READY or a FAULT is asserted.

2) **READY**
- Pattern: solid ON
- Active only when the main application service is confirmed running (`systemd active`).

3) **FAULT: MAIN SERVICE FAILED**
- Pattern: **2 quick blinks** then long pause (loop)
  - 0.15s ON / 0.15s OFF repeated 2 times
  - then 1.2s OFF pause

4) **FAULT: WIFI NOT CONNECTED**
- Pattern: **3 quick blinks** then long pause (loop)
  - same timing, 3 blinks

5) **FAULT: NETWORK OK BUT NO INTERNET** (etc example)
- Pattern: **4 quick blinks** then long pause (loop)

6) **FAULT: DISK LOW / DISK FULL** (etc example)
- Pattern: **5 quick blinks** then long pause (loop)

### Fault priority (highest wins if multiple faults)
1. Disk low (5)
2. Service failed (2)
3. Wi-Fi not connected (3)
4. No internet (4)
Else READY or BOOTING.

---

## Part B — Architecture / Implementation Requirements

### 1) GPIO ownership: single daemon
Implement a single long-running “LED daemon” that exclusively owns GPIO12 to avoid races.
Suggested files (adjust to repo conventions):
- `hardware/status_led.py` (core GPIO + patterns)
- `hardware/status_led_daemon.py` (fault checks + mode selection + loop)

**Must support:**
- BCM numbering
- `set_mode("booting" | "ready" | "fault_service" | "fault_wifi" | "fault_internet" | "fault_disk")`
- clean shutdown: LED OFF on exit; GPIO cleanup
- no silent failures: log exceptions clearly

Library choice:
- Prefer `gpiozero` if already used/available; otherwise use `RPi.GPIO`.
- Keep dependencies minimal and documented.

### 2) Detection rules (implement these checks)

**Wi-Fi not connected (fault_wifi):** consider connected only if:
- interface `wlan0` exists AND
- it has an IPv4 address AND
- an SSID is present (e.g., `iwgetid -r` returns non-empty) OR a reliable network state indicates up

**No internet (fault_internet):** only if Wi-Fi connected.
- Confirm internet with a short-timeout check (prefer TCP connect over ICMP):
  - example: TCP connect to `1.1.1.1:443` or `8.8.8.8:53` (timeout ~2s)
  - optionally DNS resolve + connect, but do not hang if DNS is broken

**Disk low (fault_disk):**
- check `/` free space < threshold (configurable constant, default 5%)

**Service failed (fault_service):**
- if the main application systemd service is not `active`
- avoid false positives during early boot by using systemd ordering, not sleeps

### 3) Configuration (single source of truth)
Add constants near top of module (or a tiny config file) for:
- `GPIO_PIN = 12`
- disk threshold percent
- internet check targets + timeouts
- main service name (whatever this repo uses — define it once and reference it)

---

## Part C — systemd integration (required; no sleeps)

Goal: LED reflects system truth via systemd lifecycle.

### Required behavior
- On boot: LED enters **BOOTING** pattern early.
- When main app is truly running: LED becomes **READY** (solid ON).
- If main app stops/crashes: LED switches to **FAULT: SERVICE FAILED** (2 blinks) unless a higher-priority fault is present.
- If Wi-Fi drops: LED switches to **FAULT: WIFI** (3 blinks), etc.

### Implementation approach (choose one, but keep it deterministic)
Preferred: one dedicated daemon service, started at boot, that:
- starts in BOOTING
- waits for systemd + network targets (ordering, not sleeps)
- continuously evaluates faults + main service state
- updates LED accordingly

Create/update systemd units under repo-managed path, e.g.:
- `systemd/jv-status-led.service` (new)
- (optional) `systemd/jv-status-led.path` or timers not required; keep simple

The LED daemon service should:
- `Restart=always`
- run as a user that has GPIO access (usually root on Pi OS; that’s acceptable here)
- use `After=multi-user.target network-online.target`
- use `Wants=network-online.target`

**Important:** do NOT let READY be set via a blind `ExecStartPost` alone; the daemon must continuously correct state if Wi-Fi drops or the service fails.

---

## Part D — GUI: Add “Shutdown” Button

### Requirement
Codex must add a **Shutdown** button to the existing GUI that triggers a **safe system shutdown**.

“Safe shutdown” means:
- requests system shutdown via OS (systemd)
- no abrupt power cut
- should return a user-visible confirmation in the UI (“Shutting down…”)

### Implementation details (must be secure and reliable)
1) Add a GUI control labeled exactly:
- **Shutdown**

2) On click:
- call an existing backend route/controller if the app is web-based, or a Python handler if local GUI
- trigger shutdown command:
  - preferred: `systemctl poweroff`
  - acceptable: `shutdown -h now`
- use a short delay before actual shutdown only if needed to return the UI response (but do NOT rely on sleeps for correctness)

3) Permissions:
- If the GUI/backend process is not running as root, add a safe mechanism:
  - Option A (preferred): a dedicated systemd oneshot service `jv-poweroff.service` that runs `systemctl poweroff`, and the GUI calls `systemctl start jv-poweroff.service`
  - Option B: sudoers rule allowing only the required command with no password
- Do NOT grant broad sudo privileges.

4) Safety / UX:
- Add a confirmation dialog (e.g., “Are you sure?”) to prevent misclick shutdown.
- Ensure errors are shown in the UI if shutdown request fails (permission denied, missing systemd, etc.).
- The UI should not just close locally; it should explicitly show status.

### Headless compatibility
Shutdown button must work in headless mode where the UI is accessed remotely (if web UI), or when GUI runs locally. Do not require a desktop environment if the system is headless + web-based.

---

## Part E — Documentation

Update `README.md` and add `docs/STATUS_LED.md`:

### README additions
- Wiring: GPIO12 → resistor → LED → GND (BCM numbering)
- LED meanings:
  - 1 Hz blink = booting
  - solid ON = ready
  - 2 blinks = service failed
  - 3 blinks = wifi not connected
  - 4 blinks = no internet
  - 5 blinks = disk low
- Shutdown button behavior + confirmation
- Troubleshooting notes (if LED never goes solid, service did not become active)

### STATUS_LED.md checklist
Manual verification steps:
- boot: observe 1 Hz blink
- when app running: solid ON
- stop app service: 2-blink fault
- disconnect wifi: 3-blink fault
- break internet route: 4-blink fault
- simulate disk low by temporarily raising threshold: 5-blink fault
- click Shutdown: system powers off safely

---

## Acceptance Criteria (must pass)
- GPIO 12 is used in BCM mode
- LED is OFF at process exit; no stuck ON after stop
- No boot “sleep hacks”
- LED state is accurate during runtime changes (wifi drop, service crash)
- Shutdown button works reliably and safely, with confirmation + error reporting
- Docs updated and accurate
- No new installers or binaries introduced

---

## Notes / Constraints
- Keep changes minimal and consistent with the repo’s existing structure.
- Prefer standard library + minimal Pi packages.
- Do not break existing behavior unrelated to LED/shutdown.

END PROMPT
