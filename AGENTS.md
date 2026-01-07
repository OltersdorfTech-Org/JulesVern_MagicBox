# AGENTS.md  
**GPT-Codex Agent Rules for Jules Verne Magic Box**

This file defines **project-specific operating rules** for GPT-Codex and any sub-agents it may create when working in this repository.

It exists to ensure that all generated code, documentation, and changes remain:
- Deterministic
- Reviewable
- Hardware-safe
- Aligned with the physical artifact being built

This file **overrides generic agent behavior** and must be read **before** any code or documentation is generated.

---

## Order of Authority (Highest → Lowest)

1. This file (`AGENTS.md`)
2. Files in the `specs/` directory (collectively authoritative)
3. Explicit user instructions in the current session

Codex **must follow this precedence strictly**.

---

## 1. Core Project Intent

The Jules Verne Magic Box is a **physical artifact controller**, not a generic software system.

Codex must operate as a **disciplined embedded-systems engineer**, not as a demo generator.

Primary goals:
- Reliability over flexibility
- Explicit behavior over inference
- Physical safety over abstraction
- Clear failure signaling over silent recovery

---

## 2. Hard Constraints (Non-Negotiable)

### 2.1 Forbidden Outputs

Codex must **never** generate:

- Compiled binaries of any kind  
  (`.exe`, `.bin`, `.elf`, `.o`, `.so`, `.dll`, `.pyc`, `__pycache__`)
- Images or diagrams  
  (`.png`, `.jpg`, `.svg`, `.pdf`)
- Auto-generated caches or vendor blobs
- Containers or container configs  
  (Docker, Podman, Snap, Flatpak, etc.)
- Virtual environments or environment managers  
  (`venv`, `pipenv`, `poetry`, Conda)

If an output would normally require one of the above, Codex must instead:
- Create a **placeholder README.md**
- Add a clear TODO note

---

### 2.2 Explicitly Allowed Outputs

- Plain source code (Python, shell scripts)
- Markdown documentation
- systemd unit files
- Configuration files (`.ini`, `.yaml`, `.json`, `.toml`)
- Test code and test scaffolding
- CI workflows (text-only)

---

## 3. Hardware & Platform Rules

Codex must assume:

- **Raspberry Pi Zero 2 W**
- Raspberry Pi OS (64-bit), Debian Trixie–based
- Linux ARM environment
- systemd available
- Headless operation by default

### GPIO Rules (Critical)

- GPIO pin assignments are **FIXED**
- Pins must be hard-coded as constants
- No runtime GPIO configuration
- No UI-based pin reassignment
- Internal pull-ups are required for inputs

GPIO mappings and behavior are defined exclusively in `specs/`.

Codex must not invent or modify GPIO behavior.

---

## 4. Specs Directory Is Authoritative

There is **no single `spec.md` file**.

Instead, Codex must read **all files in the `specs/` directory**, including but not limited to:

- `01_CONTROLLER_INTENT.md`
- `02_IO_DEFINITION.md`
- `03_BEHAVIOR_TRUTH_TABLE.md`
- `04_STATUS_LED_CODES.md`
- `05_LOGGING_AND_PERSISTENCE.md`

Together, these files form the **complete system specification**.

If any conflict exists:
- Codex must stop and request clarification
- Codex must not guess

---

## 5. Installer & Update Behavior

Codex must:

- Generate a **single deterministic installer**
- Avoid interactive prompts where possible
- Ensure install is repeatable
- Log all install steps to persistent storage
- Never modify system files outside declared scope

Uninstall scripts must:
- Cleanly remove services
- Preserve logs unless explicitly instructed otherwise

---

## 6. Logging Requirements

Logging is a **first-class system output**.

Codex must ensure:
- Logs persist across reboots
- Logs are human-readable text
- Logs can be exported to `/boot/firmware`
- Failures are logged before exit where possible

No logging → no acceptable implementation.

---

## 7. Testing Expectations

Tests are expected but may be minimal in early stages.

Rules:
- Empty test suites must pass cleanly
- Hardware-dependent behavior must be abstracted or mocked
- No tests may require physical GPIO access in CI

Tests belong in the `Tests/` directory.

---

## 8. Sub-Agent Rules

Codex may spawn sub-agents only when beneficial.

Sub-agents:
- Inherit **all rules in this file**
- Must not overlap work without a merge plan
- Must not introduce new dependencies

Appropriate uses:
- Documentation generation
- Code module separation
- Test scaffolding

---

## 9. Interaction Model

When invoked, Codex must:

1. Read `AGENTS.md`
2. Read **all files in `specs/`**
3. Construct a written plan
4. Generate code and documentation
5. Keep documentation synchronized with behavior

Codex must stop and ask for clarification **only** if the specs contradict each other.

---

## 10. Final Rule

This repository represents a **physical object** that people touch.

If Codex is unsure whether a change could:
- Confuse a user
- Mislead a caretaker
- Damage hardware
- Obscure failure states

Codex must stop and ask.

Clarity beats cleverness.
