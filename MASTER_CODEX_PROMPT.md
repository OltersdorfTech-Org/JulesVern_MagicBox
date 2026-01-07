# MASTER_CODEX_PROMPT.md
**Jules Verne Magic Box — Master Prompt for GPT-Codex (Authoritative)**

You are GPT-Codex operating on the repository:
**OltersdorfTech-Org/JulesVern_MagicBox**

Your task: generate a clean, working v1 system implementation under `src/` that matches the project’s specifications exactly.

This repository represents a **physical device**. Favor determinism, safety, and clarity.

---

## 0) Order of Authority (MUST FOLLOW)

1. `AGENTS.md` (repo root)
2. All files in `specs/` (collectively authoritative)
3. This file (`MASTER_CODEX_PROMPT.md`)
4. Any explicit user instructions in the current Codex session

If anything conflicts, stop and ask for clarification. Do not guess.

---

## 1) Hard Prohibitions (NON-NEGOTIABLE)

You must NOT generate, commit, or include:

### Binaries / compiled artifacts
- `.exe`, `.dll`, `.so`, `.bin`, `.elf`, `.o`, `.a`, `.wasm`
- `.pyc`, `__pycache__/`
- Any compiled frontend bundles or vendor blobs

### Images / diagrams
- `.png`, `.jpg`, `.jpeg`, `.svg`, `.pdf`
- Do not add images to the repo. Use **markdown placeholders** only.

### Virtual environments / containers
- No `venv`, Poetry, Pipenv, Conda
- No Docker/Podman/Snap/Flatpak

### Network-setup automation
- Do not modify Wi-Fi settings or create an AP.
- Networking is assumed to exist; failures are signaled via Status LED + logs.

If you need placeholders, create `README.md` files in the relevant folders.

---

## 2) Repository Structure (MUST MATCH)

You must preserve and/or create the following structure:

```
/
├─ README.md
├─ AGENTS.md
├─ INSTALL_WINDOWS.md
├─ WIRING_GUIDE.md
├─ USAGE_GUIDE.md
├─ Tests/
│  └─ README.md
├─ Wiring_Diagram/
│  └─ README.md
├─ assets/
│  └─ README.md
├─ specs/
│  ├─ 01_CONTROLLER_INTENT.md
│  ├─ 02_IO_DEFINITION.md
│  ├─ 03_BEHAVIOR_TRUTH_TABLE.md
│  ├─ 04_STATUS_LED_CODES.md
│  ├─ 05_LOGGING_AND_PERSISTENCE.md
└─ src/
   ├─ installer.sh
   ├─ uninstall.sh
   ├─ magicbox/
   │  ├─ __init__.py
   │  ├─ main.py
   │  ├─ config.py
   │  ├─ logging_util.py
   │  ├─ gpio_io.py
   │  ├─ leds.py
   │  ├─ webui.py
   │  ├─ health.py
   │  └─ log_export.py
   └─ systemd/
      └─ magicbox.service
```

You may add files under `src/` if needed, but keep it minimal and well-explained.

---

## 3) Target Platform (LOCKED)

- Raspberry Pi Zero 2 W
- Raspberry Pi OS (64-bit), Debian Trixie-based
- systemd is present
- Headless default operation
- Python 3 system install (no venv)

---

## 4) Functional Requirements (MUST IMPLEMENT)

Read and implement all rules from `specs/` exactly.

At minimum the system must provide:

### 4.1 GPIO (fixed pins, no configurability)
- Inputs (internal pull-ups, GPIO→GND switches):
  - GPIO 27 Lid
  - GPIO 05 Key1
  - GPIO 06 Key2
- Outputs (GPIO→resistor→LED→GND):
  - GPIO 12 Status LED
  - GPIO 04 Message LED
  - GPIO 13 Key1 LED
  - GPIO 19 Key2 LED
  - GPIO 26 Magic LED

### 4.2 Web UI (local LAN)
Web UI controls:
- Toggle: Message/Object Received (I4)
- Toggle: GPIO Enable/Disable (I5 master gate for interactive LEDs)
- Action: Show Logs (I7)
- Action: Export Logs (I6)

### 4.3 Behavior truth table
Implement behaviors from `03_BEHAVIOR_TRUTH_TABLE.md`, including:
- Key switches control Key LEDs
- Message toggle controls Message LED
- Lid open triggers Magic LED **only if Message toggle is ON**, random flash for 30 seconds
- I5 gate forces {Message LED, Key1 LED, Key2 LED, Magic LED} OFF always when disabled
- Status LED always active

### 4.4 Status LED codes
Implement all patterns in `04_STATUS_LED_CODES.md` with correct timing and priority rules.

### 4.5 Logging & persistence
Implement `05_LOGGING_AND_PERSISTENCE.md` requirements:
- Persistent logs in `/var/log/magicbox/`
- Rotating file logs
- Installer logs to `/var/log/magicbox/installer.log`
- Export logs to `/boot/firmware/MAGICBOX_LOGS/`
- Log export must be usable without SSH (triggered via Web UI)
- All exceptions must be logged with tracebacks

---

## 5) Architecture Requirements (HOW TO BUILD IT)

### 5.1 Process model
The system should run as ONE systemd service:
- `magicbox.service`
- Starts on boot
- Restarts on failure with reasonable limits

### 5.2 Concurrency
Use a simple model:
- Main thread: run web server
- Background tasks/threads:
  - GPIO input polling / debouncing
  - LED status renderer thread (Status LED + interactive LEDs updates)
  - Health checks (Wi-Fi presence, web server health state)
  - Magic LED effect task (30 sec, cancellable)

Must be robust: no busy-waiting; no unbounded thread creation.

### 5.3 GPIO library
Prefer standard Raspberry Pi Python GPIO solutions that work on Pi OS 64-bit:
- Prefer `gpiozero` (recommended) OR `RPi.GPIO` if installed and stable.
- If using `gpiozero`, ensure internal pull-ups are configured properly.
- Avoid experimental libraries unless necessary.

### 5.4 Web framework
Use a minimal web server:
- Prefer `Flask` for simplicity
- Must serve on `0.0.0.0:80` OR `0.0.0.0:5000` (choose and document)
- If binding to port 80, handle permissions (systemd can run as root; document why)
- Web pages can be minimal HTML with basic forms/buttons; no heavy JS required.

### 5.5 Configuration
- `src/magicbox/config.py` contains constants only (pins, timing, paths)
- No user-editable pin config
- No runtime config files required for v1 (except logs and systemd unit)

---

## 6) Installer / Uninstaller Requirements

### installer.sh
Must:
- Be non-interactive where possible
- Install apt dependencies
- Install Python dependencies via pip (system-level or isolated to a known location; no venv)
- Create `/var/log/magicbox/` and set permissions
- Install systemd unit from `src/systemd/magicbox.service`
- `systemctl daemon-reload`
- `systemctl enable magicbox.service`
- `systemctl restart magicbox.service`
- Write a detailed installer log to `/var/log/magicbox/installer.log`
- If any step fails, log it and exit non-zero

### uninstall.sh
Must:
- Stop and disable the systemd service
- Remove installed unit file
- `systemctl daemon-reload`
- Remove only files installed by the project
- Preserve logs by default (unless user passes a flag like `--purge-logs`)

---

## 7) Documentation Updates (MUST KEEP IN SYNC)

If your implementation choices differ from any documentation, you must update docs.

However:
- Do not add images
- Do not change fixed GPIO mapping
- Keep README clean and accurate

---

## 8) Testing (minimal but required)

Add a minimal test scaffold under `Tests/` that:
- Imports the core modules successfully
- Can run without GPIO hardware (use mocks)
- Does not require network access

If you add a CI workflow, keep it text-only and avoid OS-specific assumptions.
(If no CI is added in this repo phase, tests must still be runnable manually.)

---

## 9) Implementation Checklist (YOU MUST SELF-VERIFY)

Before opening a PR, verify:
- No forbidden file types exist
- No images were added
- No `__pycache__` exists
- `installer.sh` runs and logs to `/var/log/magicbox/installer.log`
- Service starts on boot and shows correct Status LED patterns
- Web UI toggles work and enforce the GPIO master gate
- Log export writes to `/boot/firmware/MAGICBOX_LOGS/`
- All errors are visible via Status LED and recorded in logs

---

## 10) Deliverable

Open a PR that includes:
- All `src/` code, installer, uninstaller, and systemd service
- Any required doc updates (text-only)
- Tests scaffold under `Tests/`

Do not include binaries, images, or compiled artifacts.

Done means: **a fresh Pi OS install can be set up from Windows, installed, wired, and used reliably** according to `specs/`.
