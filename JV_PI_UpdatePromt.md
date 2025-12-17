You are GPT-Codex working inside the JulesVern_MagicBox repository.

SOURCE OF TRUTH / PROCESS RULES
- Read and follow ./AGENTS.md first. Treat it as the authority on workflow, coding style, testing, and repo conventions.
- This prompt and AGENTS.md override any other assumptions.
- Do NOT add binaries or large generated assets. Text/code only.
- Make minimal, surgical changes. Preserve existing behavior unless explicitly changed below.
- Only ask clarifying questions if you cannot locate the relevant code/files in-repo. Otherwise proceed.

CONTEXT (CURRENT UI)
Current web UI has 3 buttons:
- "turn remote LID on"
- "turn remote Lid off"
- "toggle remote lid"
They target the existing "remote LID Flag" (also referred to as "remote lid Flag").

GOAL
Adjust the remote control Flask web interface:

1) Replace current 3 buttons with 2 toggle buttons:
   - Button 1 label: "LID LED Toggle"
     - Behavior: toggle the existing "remote LID Flag"
   - Button 2 label: "magic flicker toggle"
     - Behavior: toggle "Magic Flag" (the flag that enables/disables the magic LED flickering)

2) Move flag indicators:
   - Indicators currently shown at the bottom must be moved next to the appropriate button.
   - Indicator style: "ON"/"OFF" text with red/green color (red = OFF, green = ON).
   - Indicators should reflect current flag state (remote LID flag next to LID LED Toggle, Magic Flag next to magic flicker toggle).

3) Add Safety (third control):
   - Add a third control: "Safety" enable/disable (button or switch UI is fine).
   - This is a GLOBAL enable/disable for ALL GPIO outputs and ALL switch inputs.
   - When Safety is DISABLED:
     - The UI must block everything: both toggles should be disabled (not clickable) and/or routes should refuse actions with a clear message.
     - Flags should not be changed while safety is disabled (block everything).
   - Default on boot: DISABLED (safety off).
   - Show safety state in the UI prominently.

4) Add GPIO pin configuration section at the bottom of the page:
   - A table-based interface for user input of GPIO pin numbers using PHYSICAL header pin numbering in the UI.
   - Configurable signals (exact keys/labels):
     - lid_switch_pin
     - lid_led_pin
     - magic_flicker_led_pin
     - Key1LED PIN
     - Key2LED PIN
     - Key1switch PIN
     - Key2switch PIN
   - Validate input:
     - must be integer
     - reject blank/invalid with a clear UI error message
   - Submitting updates must update the existing config file:
     - config.py is the authoritative config storage.
     - Implement config updates carefully (avoid corrupting config.py; preserve non-related settings).
     - Do not introduce a new config system unless absolutely necessary.

5) Include a simple diagram of the Raspberry Pi header pin numbering:
   - Must be text-only (ASCII) so no binary images.
   - Include it in the web UI near the GPIO table AND in README.md.
   - Diagram should help the user identify physical pin numbers clearly.

6) Update README.md:
   - Document the new UI:
     - 2 toggles + indicators next to them
     - safety enable/disable behavior and default (disabled on boot)
     - GPIO table section and what it edits in config.py
   - Enhance Windows 10/11 install steps (File Explorer only):
     - Show the latest process for mounting/accessing the boot/firmware partitions on Windows and manually copying the repo folder to the SD card.
     - No git clone required on the Pi.
   - Include Pi-side bash commands:
     - Move the copied repo folder from the boot/firmware partition to the user’s home directory (e.g., ~/src or ~/JulesVern_MagicBox), and then run/install from there.

IMPLEMENTATION REQUIREMENTS
- Maintain existing Flask structure, templates, and route style per AGENTS.md.
- No heavy JS frameworks; keep UI simple.
- Safety enforcement must exist both in UI (disable buttons) AND server-side (routes refuse when safety disabled).
- Use the repo’s existing flag/state storage patterns. Do not invent a new flag persistence method unless required.
- Add/adjust tests if the repo already has a testing pattern; otherwise add minimal sanity checks per AGENTS.md.

STEP-BY-STEP PLAN (MANDATORY)
1) Open and summarize AGENTS.md requirements you will follow.
2) Locate Flask app entrypoint, routes, templates, and current button/indicator implementation.
3) Identify how/where:
   - remote LID Flag is stored
   - Magic Flag is stored (or add it using the existing pattern if missing)
   - Safety state is stored (must default to disabled on boot; persist using existing state mechanism)
4) Implement UI + backend changes:
   - Update templates: 2 toggle buttons + indicators next to them; add safety control; add GPIO table section + ASCII pin diagram.
   - Update routes: handle toggles, safety toggle, and GPIO config save.
   - Enforce safety in routes.
   - Implement safe updating of config.py fields for the specified pins.
5) Update README.md per requirements, including Windows manual copy + Pi bash move commands.
6) Run formatting/lint/tests
7) Produce final summary + file list of changes.

OUTPUT FORMAT
- Provide a concise summary of changes.
- List modified files and what changed in each.
- Include any commands to run tests/formatters per AGENTS.md.
- No binaries.

NOW BEGIN:
Read AGENTS.md and then inspect the current Flask UI implementation (routes/templates). If and only if you cannot locate critical implementation details in the repo, ask targeted clarification questions; otherwise proceed to implement.
