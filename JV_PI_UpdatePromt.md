You are GPT-Codex working inside the JulesVern_MagicBox repository.

NON-NEGOTIABLE RULES
- Read ./AGENTS.md first and follow it strictly.
- No binaries. No images. No downloaded installers. Text/code only.
- No ambiguous instructions in docs. Every step must be explicit and copy/pasteable.
- Target device: Raspberry Pi Zero 2 W running the latest Raspberry Pi OS (Bookworm).
- Goal: installation should feel “drag-and-drop” (copy folder to SD) or “point-and-click” (run one obvious installer script). No git clone required on the Pi.

PRIMARY OUTCOME
Make the project dramatically easier to install and run on a Pi Zero 2 W on the latest OS, with:
1) A “copy to SD card” workflow from Windows (File Explorer) and/or
2) A single, obvious “Install” action on the Pi (double-click or one command)

DELIVERABLES (MUST PRODUCE)
A) A new installer script:
   - Location: scripts/install_pi.sh (or the repo’s preferred scripts folder per AGENTS.md)
   - Must be idempotent (safe to run multiple times)
   - Must work on Bookworm
   - Must:
     1. Verify it’s on a Pi/Linux (and warn if not)
     2. Create a Python venv in a predictable location (e.g., .venv)
     3. Install Python deps in a Pi-friendly way (prefer apt for system libs + pip for python packages, but do not guess: inspect existing requirements and current install steps)
     4. Set up a systemd service to run the Magic Box on boot (and a way to stop/disable it)
     5. Create a simple “Run Magic Box” helper command or launcher (see section D)
     6. Print a final “SUCCESS” message with exactly what to do next

B) A new “first-boot SD card copy” workflow (Windows drag-and-drop):
   - Add a folder at repo root: sdcard_bootstrap/
   - It must contain ONLY text files (no binaries) that a user can copy onto the SD card’s boot/firmware partition from Windows File Explorer.
   - Bookworm note: SD boot partition is typically visible in Windows and is commonly called “bootfs”; on the Pi it mounts at /boot/firmware.
   - Provide a mechanism so that on the Pi’s first boot, it can finish installation automatically OR make the next step a single click/command.
   - Acceptable options (choose the most reliable for Bookworm):
     - systemd unit placed via boot partition then moved into place by the installer
     - a clearly documented manual step that is ONE command on the Pi, nothing more
   - If full auto-first-boot is too fragile, implement “near-auto”:
     - user copies folder to boot partition
     - user boots Pi
     - user runs ONE obvious command shown in README (example: sudo /boot/firmware/JulesVern_MagicBox/install.sh)

C) Documentation overhaul (crystal clear):
   - Update README.md and/or create docs/INSTALL_PI_ZERO_2W.md
   - Must include:
     1. “Windows SD Card Method (No Git)” — File Explorer drag-and-drop steps
     2. “Pi Method (One Command)” — exact command(s), exactly once
     3. How to start/stop/check status (systemd commands)
     4. Where logs are (journalctl commands)
     5. Common failure modes and exact fixes (missing python, permissions, wrong path, etc.)
   - Use absolute paths and explicit filenames. No vague phrases like “copy it somewhere” or “run the script”.

D) Point-and-click / obvious UX:
   - Provide at least ONE of the following (text only; no binaries):
     1) A desktop launcher (.desktop file) that runs the installer or launches the UI
     2) A single script named INSTALL_MAGIC_BOX.sh at repo root that users can double-click in Raspberry Pi OS desktop
     3) A “magicbox” command installed into /usr/local/bin that provides:
        - magicbox install
        - magicbox start
        - magicbox stop
        - magicbox status
     - Choose the approach most compatible with Pi Zero 2 W constraints and AGENTS.md conventions.

STRICT TECHNICAL CONSTRAINTS
- Pi Zero 2 W is resource constrained:
  - Avoid heavy dependencies
  - Prefer a lightweight Flask deployment suitable for a Pi (use existing approach; do not introduce Docker)
  - Use systemd, not cron hacks
- Do not change app runtime behavior except what’s necessary for install reliability.
- Do not require root except where unavoidable (systemd install, /usr/local/bin). Otherwise run as the regular user.

STEP-BY-STEP (MANDATORY)
1) Read AGENTS.md and summarize constraints you will follow.
2) Inspect current repo:
   - entrypoint(s)
   - current install instructions
   - requirements files
   - any existing systemd service files or scripts
3) Decide the simplest reliable install architecture for Bookworm.
4) Implement the scripts + service + docs.
5) Verify all paths are consistent and correct.
6) Ensure “no git required” path is fully documented.
7) review full code with lint and any other applicable tests.
8) Provide final output:
   - changed files list
   - exact install steps (copy/paste)
   - how to validate it works

OUTPUT FORMAT
- Start with a brief “What I changed” summary.
- Then list files modified/added.
- Then provide the final installation instructions exactly as they should appear to the user.
- No binaries, no images.

NOW START:
Proceed with steps 1–3. If you encounter missing specifics, do NOT ask open-ended questions. Ask only targeted questions with multiple-choice options, then continue with the most conservative default that preserves existing behavior.
